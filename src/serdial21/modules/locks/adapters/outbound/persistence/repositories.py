import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from serdial21.modules.locks.adapters.outbound.persistence.models import AccountLockModel
from serdial21.modules.locks.domain.entities import AccountLock, EffectOperation, LockScope, LockStatus


def scope_fingerprint(lock: AccountLock) -> str:
    target = {'ACCOUNT': lock.account_id, 'GROUP': lock.group_id, 'MODULE': lock.module, 'COMPETENCE': lock.competence, 'EXERCISE': lock.exercise}[lock.scope.value]
    payload = json.dumps({'scope': lock.scope.value, 'target': str(target)}, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode()).hexdigest()


class SQLAlchemyAccountLockRepository:
    def __init__(self, session: Session) -> None: self._session = session
    def add(self, lock: AccountLock) -> None: self._session.add(_model(lock))
    def get(self, tenant_id: UUID, lock_id: UUID) -> AccountLock | None:
        model = self._session.scalar(select(AccountLockModel).where(AccountLockModel.tenant_id == tenant_id, AccountLockModel.id == lock_id))
        return None if model is None else _domain(model)
    def list_active(self, tenant_id: UUID, company_id: UUID) -> tuple[AccountLock, ...]:
        models = self._session.scalars(select(AccountLockModel).where(AccountLockModel.tenant_id == tenant_id, AccountLockModel.company_id == company_id, AccountLockModel.status == LockStatus.ACTIVE.value))
        return tuple(_domain(model) for model in models)
    def save(self, lock: AccountLock) -> None:
        model = self._session.scalar(select(AccountLockModel).where(AccountLockModel.tenant_id == lock.tenant_id, AccountLockModel.id == lock.id))
        if model is None: raise ValueError('lock inexistente')
        model.status, model.released_by, model.released_at, model.release_reason = lock.status.value, lock.released_by, lock.released_at, lock.release_reason
        model.active_marker = 'ACTIVE' if lock.status is LockStatus.ACTIVE else None


def _model(lock: AccountLock) -> AccountLockModel:
    return AccountLockModel(id=lock.id, tenant_id=lock.tenant_id, company_id=lock.company_id, scope=lock.scope.value, operations=[item.value for item in lock.operations], reason=lock.reason, status=lock.status.value, account_id=lock.account_id, group_id=lock.group_id, module=lock.module, competence=lock.competence, exercise=lock.exercise, released_by=lock.released_by, released_at=lock.released_at, release_reason=lock.release_reason, scope_fingerprint=scope_fingerprint(lock), active_marker='ACTIVE' if lock.status is LockStatus.ACTIVE else None)


def _domain(model: AccountLockModel) -> AccountLock:
    return AccountLock(model.id, model.tenant_id, model.company_id, LockScope(model.scope), tuple(EffectOperation(value) for value in model.operations), model.reason, LockStatus(model.status), model.account_id, model.group_id, model.module, model.competence, model.exercise, model.released_by, model.released_at, model.release_reason)
