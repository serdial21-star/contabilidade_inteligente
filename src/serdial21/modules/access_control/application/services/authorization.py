'''Política central de autorização do Serdial21.'''

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from serdial21.modules.access_control.application.ports.authorization import (
    AuthorizationRepository,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.shared_kernel.observability import security_event


class AccessDeniedError(PermissionError):
    '''Negação estável que não revela existência em outro tenant.'''

    code = 'access_denied'

    def __init__(self) -> None:
        super().__init__('access denied')


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    tenant_id: UUID
    user_id: UUID
    permission: PermissionCode
    company_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AuthorizedContext:
    tenant_id: UUID
    user_id: UUID
    membership_id: UUID
    company_id: UUID | None
    permission: PermissionCode
    authorized_at: datetime


class AuthorizationService:
    '''Revalida identidade, membership, empresa, acesso e permissão.'''

    def __init__(self, repository: AuthorizationRepository) -> None:
        self._repository = repository

    def require(
        self,
        request: AuthorizationRequest,
        *,
        at: datetime | None = None,
        role_name: str | None = None,
    ) -> AuthorizedContext:
        checked_at = at or datetime.now(UTC)
        if checked_at.tzinfo is None or checked_at.utcoffset() is None:
            raise ValueError('instante de autorização deve possuir timezone')

        if not self._repository.is_user_active(request.user_id):
            self._deny('inactive_user')

        membership_id = self._repository.find_active_membership(
            request.tenant_id,
            request.user_id,
            checked_at,
        )
        if membership_id is None:
            self._deny('membership_unavailable')

        if request.company_id is not None:
            if not self._repository.company_belongs_to_tenant(
                request.tenant_id,
                request.company_id,
                checked_at,
            ):
                self._deny('company_out_of_scope')
            if not self._repository.has_active_company_access(
                request.tenant_id,
                membership_id,
                request.company_id,
                checked_at,
            ):
                self._deny('company_access_unavailable')

        if not self._repository.has_permission(
            request.tenant_id,
            membership_id,
            request.company_id,
            request.permission.value,
            checked_at,
        ):
            self._deny('permission_unavailable')

        if role_name is not None and not self._repository.has_role(
            request.tenant_id, membership_id, request.company_id, role_name, checked_at,
        ):
            self._deny('role_unavailable')

        return AuthorizedContext(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            membership_id=membership_id,
            company_id=request.company_id,
            permission=request.permission,
            authorized_at=checked_at,
        )

    @staticmethod
    def _deny(reason: str) -> None:
        security_event('authorization.denied', fields={'reason': reason})
        raise AccessDeniedError()
