'''Desbloqueio autorizado e auditado, sem retomada automática de jobs.'''

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from serdial21.modules.access_control.application.services.authorization import AuthorizedContext
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditEvent, AuditOrigin
from serdial21.modules.locks.domain.entities import AccountLock, release_lock


@dataclass(frozen=True, slots=True)
class LockReleaseOutcome:
    lock: AccountLock
    audit_event: AuditEvent
    jobs_resumed: bool = False


class AccountLockService:
    def __init__(self, audit_service: AuditService) -> None:
        self._audit_service = audit_service

    def release(self, lock: AccountLock, *, authorization: AuthorizedContext, reason: str,
                correlation_id: UUID, released_at: datetime) -> LockReleaseOutcome:
        if authorization.permission.value != 'lock.manage':
            raise PermissionError('permissão insuficiente para desbloqueio')
        if (authorization.tenant_id, authorization.company_id) != (lock.tenant_id, lock.company_id):
            raise PermissionError('permissão insuficiente para desbloqueio')
        released = release_lock(lock, actor_id=authorization.user_id, reason=reason,
                                released_at=released_at)
        audit_event = self._audit_service.record(AuditRecord(
            tenant_id=lock.tenant_id, company_id=lock.company_id,
            actor_id=authorization.user_id, origin=AuditOrigin.HUMAN, module='locks',
            action='account_lock.released', subject_type='AccountLock', subject_id=lock.id,
            subject_version=None, before={'status': lock.status.value, 'scope': lock.scope.value},
            after={'status': released.status.value, 'requires_review': True}, reason=reason,
            correlation_id=correlation_id, causation_id=None,
        ))
        return LockReleaseOutcome(released, audit_event)
