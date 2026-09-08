'''Composição persistente dos casos de uso de AccountLock em uma Session comum.'''

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from serdial21.modules.access_control.adapters.outbound.persistence.repositories import SqlAlchemyAuthorizationRepository
from serdial21.modules.access_control.application.services.authorization import AuthorizationService
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.locks.adapters.outbound.persistence.repositories import SQLAlchemyAccountLockRepository
from serdial21.modules.locks.application.services.locks import AccountLockService
from serdial21.modules.locks.application.services.persistent_locks import (
    CreateAccountLock, PersistedAccountLockGuard, ReleaseAccountLock,
)


@dataclass(frozen=True, slots=True)
class AccountLockRuntime:
    create: CreateAccountLock
    release: ReleaseAccountLock
    guard: PersistedAccountLockGuard


def create_account_lock_runtime(session: Session, *, clock: Callable[[], datetime] | None = None) -> AccountLockRuntime:
    '''Reutiliza a Session/UoW do chamador; commit e rollback pertencem a session_scope.'''
    repository = SQLAlchemyAccountLockRepository(session)
    audit = AuditService(SqlAlchemyAuditRepository(session), clock=clock)
    authorization = AuthorizationService(SqlAlchemyAuthorizationRepository(session))
    service = AccountLockService(audit)
    return AccountLockRuntime(
        create=CreateAccountLock(repository, authorization, audit, flush=session.flush, clock=clock),
        release=ReleaseAccountLock(repository, authorization, service, flush=session.flush, clock=clock),
        guard=PersistedAccountLockGuard(repository),
    )
