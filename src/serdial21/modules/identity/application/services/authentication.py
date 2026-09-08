'''Integra identidade verificada à autorização tenant-aware existente.'''

from datetime import datetime
from uuid import UUID

from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError,
    AuthorizationRequest,
    AuthorizationService,
    AuthorizedContext,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.identity.application.ports.authentication import IdentityDirectory
from serdial21.modules.identity.domain.entities import AuthenticatedPrincipal, VerifiedIdentity


class IdentityNotLinkedError(AccessDeniedError):
    '''Token válido sem vínculo interno; mantém a resposta uniforme.'''


class IdentityContextService:
    def __init__(
        self,
        directory: IdentityDirectory,
        authorization: AuthorizationService,
    ) -> None:
        self._directory = directory
        self._authorization = authorization

    def principal(self, identity: VerifiedIdentity) -> AuthenticatedPrincipal:
        user_id = self._directory.find_user_id(identity.issuer, identity.subject)
        if user_id is None:
            raise IdentityNotLinkedError()
        return AuthenticatedPrincipal(identity=identity, user_id=user_id)

    def require(
        self,
        principal: AuthenticatedPrincipal,
        permission: PermissionCode,
        *,
        company_id: UUID | None = None,
        role_name: str | None = None,
        at: datetime | None = None,
    ) -> AuthorizedContext:
        return self._authorization.require(
            AuthorizationRequest(
                tenant_id=principal.identity.tenant_id,
                user_id=principal.user_id,
                company_id=company_id,
                permission=permission,
            ),
            role_name=role_name,
            at=at,
        )
