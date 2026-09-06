'''AccountLock durável: a origem do efeito não altera a regra de bloqueio.'''

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class LockScope(StrEnum):
    ACCOUNT = 'ACCOUNT'
    GROUP = 'GROUP'
    MODULE = 'MODULE'
    COMPETENCE = 'COMPETENCE'
    EXERCISE = 'EXERCISE'


class LockStatus(StrEnum):
    ACTIVE = 'ACTIVE'
    RELEASED = 'RELEASED'


class EffectOperation(StrEnum):
    ALTER = 'ALTER'
    APPROVE = 'APPROVE'
    REPROCESS = 'REPROCESS'
    EXPORT = 'EXPORT'
    RECONCILE = 'RECONCILE'


class EffectChannel(StrEnum):
    USER = 'USER'
    API = 'API'
    IMPORT = 'IMPORT'
    INTEGRATION = 'INTEGRATION'
    JOB = 'JOB'
    AI = 'AI'
    AUTOMATION = 'AUTOMATION'


class AccountLockedError(PermissionError):
    code = 'account_locked'

    def __init__(self) -> None:
        super().__init__('account locked')


@dataclass(frozen=True, slots=True)
class AccountLock:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    scope: LockScope
    operations: tuple[EffectOperation, ...]
    reason: str
    status: LockStatus
    account_id: UUID | None = None
    group_id: UUID | None = None
    module: str | None = None
    competence: date | None = None
    exercise: int | None = None
    released_by: UUID | None = None
    released_at: datetime | None = None
    release_reason: str | None = None


@dataclass(frozen=True, slots=True)
class EffectContext:
    '''Fatos autorizados e atuais do instante do efeito; não vêm do request cru.'''

    tenant_id: UUID
    company_id: UUID
    account_id: UUID | None
    group_ids: tuple[UUID, ...]
    module: str | None
    accounting_date: date
    operation: EffectOperation
    channel: EffectChannel


@dataclass(frozen=True, slots=True)
class EffectValidation:
    '''O chamador deve marcar a conciliação associada quando review for True.'''

    reconciliation_requires_review: bool
    jobs_resumed: bool = False


def create_lock(*, tenant_id: UUID, company_id: UUID, scope: LockScope,
                operations: tuple[EffectOperation, ...], reason: str,
                account_id: UUID | None = None, group_id: UUID | None = None,
                module: str | None = None, competence: date | None = None,
                exercise: int | None = None) -> AccountLock:
    lock = AccountLock(uuid4(), tenant_id, company_id, scope, operations, reason,
                       LockStatus.ACTIVE, account_id, group_id, module, competence, exercise)
    _validate_lock(lock)
    return lock


def validate_effect(locks: tuple[AccountLock, ...], context: EffectContext) -> EffectValidation:
    '''Revalida todos os locks no ponto em que o efeito seria persistido.'''
    for lock in locks:
        _validate_lock(lock)
        if lock.status is LockStatus.ACTIVE and _matches(lock, context):
            raise AccountLockedError()
    return EffectValidation(any(lock.status is LockStatus.RELEASED and _matches(lock, context) for lock in locks))


def release_lock(lock: AccountLock, *, actor_id: UUID, reason: str,
                 released_at: datetime) -> AccountLock:
    if lock.status is not LockStatus.ACTIVE:
        raise ValueError('somente lock ativo pode ser desbloqueado')
    if not reason.strip():
        raise ValueError('desbloqueio exige justificativa')
    if released_at.tzinfo is None or released_at.utcoffset() is None:
        raise ValueError('desbloqueio exige timestamp com timezone')
    return replace(lock, status=LockStatus.RELEASED, released_by=actor_id,
                   released_at=released_at, release_reason=reason)


def _validate_lock(lock: AccountLock) -> None:
    if not lock.operations or len(set(lock.operations)) != len(lock.operations):
        raise ValueError('lock exige operações distintas')
    if not lock.reason.strip():
        raise ValueError('lock exige motivo')
    targets = (lock.account_id, lock.group_id, lock.module, lock.competence, lock.exercise)
    if sum(target is not None for target in targets) != 1:
        raise ValueError('lock exige exatamente um alvo de escopo')
    expected = {LockScope.ACCOUNT: lock.account_id, LockScope.GROUP: lock.group_id,
                LockScope.MODULE: lock.module, LockScope.COMPETENCE: lock.competence,
                LockScope.EXERCISE: lock.exercise}[lock.scope]
    if expected is None:
        raise ValueError('alvo incompatível com escopo do lock')
    if lock.scope is LockScope.COMPETENCE and lock.competence is not None and lock.competence.day != 1:
        raise ValueError('competência deve ser representada pelo primeiro dia do mês')
    if lock.scope is LockScope.EXERCISE and (lock.exercise is None or lock.exercise < 1):
        raise ValueError('exercício inválido')


def _matches(lock: AccountLock, context: EffectContext) -> bool:
    if (lock.tenant_id, lock.company_id) != (context.tenant_id, context.company_id):
        return False
    if context.operation not in lock.operations:
        return False
    if lock.scope is LockScope.ACCOUNT:
        return lock.account_id == context.account_id
    if lock.scope is LockScope.GROUP:
        return lock.group_id in context.group_ids
    if lock.scope is LockScope.MODULE:
        return lock.module == context.module
    if lock.scope is LockScope.COMPETENCE:
        return lock.competence == context.accounting_date.replace(day=1)
    return lock.exercise == context.accounting_date.year
