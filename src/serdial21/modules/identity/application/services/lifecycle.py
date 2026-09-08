'''Onboarding/offboarding autorizados, auditados e sem credenciais locais.'''

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.identity.application.ports.lifecycle import (
    IdentityLifecycleRepository,
    OffboardingChanges,
)
from serdial21.modules.identity.application.services.authentication import IdentityContextService
from serdial21.modules.identity.domain.entities import AuthenticatedPrincipal


class IdentityLifecycleDeniedError(PermissionError):
    def __init__(self) -> None:
        super().__init__('access denied')


class IdentityLifecycleConflictError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OnboardIdentity:
    issuer: str
    subject: str
    display_name: str
    email: str | None
    relationship_type: str
    company_ids: tuple[UUID, ...]
    role_id: UUID
    reason: str
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class OnboardingResult:
    user_id: UUID
    membership_id: UUID


class IdentityLifecycleService:
    def __init__(
        self,
        repository: IdentityLifecycleRepository,
        contexts: IdentityContextService,
        audit: AuditService,
        *,
        allowed_issuer: str,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._contexts = contexts
        self._audit = audit
        self._allowed_issuer = allowed_issuer.rstrip('/')
        self._clock = clock or (lambda: datetime.now(UTC))

    def onboard(
        self,
        actor: AuthenticatedPrincipal,
        command: OnboardIdentity,
    ) -> OnboardingResult:
        now = self._now()
        authorized = self._contexts.require(
            actor, PermissionCode('identity.manage'), at=now,
        )
        if command.issuer.rstrip('/') != self._allowed_issuer:
            raise IdentityLifecycleDeniedError()
        if not command.subject.strip() or len(command.subject) > 255:
            raise ValueError('subject externo inválido')
        if not command.display_name.strip() or len(command.display_name) > 200:
            raise ValueError('nome de exibição inválido')
        if not command.relationship_type.strip() or len(command.relationship_type) > 64:
            raise ValueError('tipo de relacionamento inválido')
        company_ids = tuple(dict.fromkeys(command.company_ids))
        if not company_ids:
            raise ValueError('ao menos uma empresa é obrigatória')
        if not self._repository.role_is_active(authorized.tenant_id, command.role_id):
            raise IdentityLifecycleDeniedError()
        if not self._repository.companies_are_active(
            authorized.tenant_id, company_ids, now,
        ):
            raise IdentityLifecycleDeniedError()

        user_id = self._repository.find_user_id(self._allowed_issuer, command.subject)
        if user_id is None:
            user_id = self._repository.create_user(
                self._allowed_issuer, command.subject,
                command.display_name.strip(), command.email,
            )
        else:
            if self._repository.has_active_membership(authorized.tenant_id, user_id, now):
                raise IdentityLifecycleConflictError('identidade já vinculada ao tenant')
            self._repository.activate_user(user_id, command.display_name.strip(), command.email)

        membership_id = self._repository.create_membership(
            authorized.tenant_id, user_id, command.relationship_type.strip(), now,
        )
        for company_id in company_ids:
            self._repository.grant_company_role(
                authorized.tenant_id, membership_id, company_id, command.role_id, now,
            )
        self._audit.record(AuditRecord(
            tenant_id=authorized.tenant_id,
            company_id=None,
            actor_id=authorized.user_id,
            origin=AuditOrigin.API,
            module='identity',
            action='identity.onboarded',
            subject_type='User',
            subject_id=user_id,
            subject_version=1,
            before=None,
            after={
                'membership_status': 'active',
                'company_access_count': len(company_ids),
                'role_binding_count': len(company_ids),
            },
            reason=command.reason,
            correlation_id=command.correlation_id,
        ))
        return OnboardingResult(user_id=user_id, membership_id=membership_id)

    def offboard(
        self,
        actor: AuthenticatedPrincipal,
        target_user_id: UUID,
        *,
        reason: str,
        correlation_id: UUID,
    ) -> OffboardingChanges:
        now = self._now()
        authorized = self._contexts.require(
            actor, PermissionCode('identity.manage'), at=now,
        )
        if authorized.user_id == target_user_id:
            raise IdentityLifecycleDeniedError()
        changes = self._repository.offboard(authorized.tenant_id, target_user_id, now)
        if changes is None:
            raise IdentityLifecycleDeniedError()
        self._audit.record(AuditRecord(
            tenant_id=authorized.tenant_id,
            company_id=None,
            actor_id=authorized.user_id,
            origin=AuditOrigin.API,
            module='identity',
            action='identity.offboarded',
            subject_type='User',
            subject_id=target_user_id,
            subject_version=None,
            before={'membership_status': 'active'},
            after={
                'membership_status': 'revoked',
                'company_accesses_revoked': changes.revoked_company_accesses,
                'role_bindings_revoked': changes.revoked_role_bindings,
                'user_deactivated': changes.user_deactivated,
            },
            reason=reason,
            correlation_id=correlation_id,
        ))
        return changes

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('clock de identidade exige timezone')
        return value.astimezone(UTC)
