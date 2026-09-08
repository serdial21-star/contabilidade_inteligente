'''Casos de uso transacionais para locks persistidos.

O chamador abre ``session_scope``. Repositórios e auditoria compartilham a
mesma Session e este módulo nunca confirma uma transação por conta própria.
'''

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from serdial21.modules.access_control.application.services.authorization import (
    AuthorizationRequest,
    AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.locks.application.ports.repository import AccountLockRepository
from serdial21.modules.locks.application.services.locks import AccountLockService
from serdial21.modules.locks.domain.entities import (
    AccountLock,
    EffectContext,
    EffectValidation,
    LockScope,
    EffectOperation,
    create_lock,
    validate_effect,
)


class AccountLockConflictError(ValueError):
    '''Uma chave de escopo já possui lock ativo; não expõe detalhe do banco.'''


@dataclass(frozen=True, slots=True)
class CreateAccountLockCommand:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID
    scope: LockScope
    operations: tuple[EffectOperation, ...]
    reason: str
    correlation_id: UUID
    account_id: UUID | None = None
    group_id: UUID | None = None
    module: str | None = None
    competence: date | None = None
    exercise: int | None = None


@dataclass(frozen=True, slots=True)
class ReleaseAccountLockCommand:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID
    lock_id: UUID
    reason: str
    correlation_id: UUID


class CreateAccountLock:
    def __init__(self, repository: AccountLockRepository, authorization: AuthorizationService,
                 audit: AuditService, *, flush: Callable[[], None],
                 clock: Callable[[], datetime] | None = None) -> None:
        self._repository = repository
        self._authorization = authorization
        self._audit = audit
        self._flush = flush
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(self, command: CreateAccountLockCommand) -> AccountLock:
        context = self._authorization.require(AuthorizationRequest(
            command.tenant_id, command.actor_id, PermissionCode('lock.manage'), command.company_id,
        ), at=self._now())
        lock = create_lock(
            tenant_id=command.tenant_id, company_id=command.company_id,
            scope=command.scope, operations=command.operations, reason=command.reason,
            account_id=command.account_id, group_id=command.group_id, module=command.module,
            competence=command.competence, exercise=command.exercise,
        )
        self._repository.add(lock)
        self._audit.record(AuditRecord(
            tenant_id=lock.tenant_id, company_id=lock.company_id, actor_id=context.user_id,
            origin=AuditOrigin.HUMAN, module='locks', action='account_lock.created',
            subject_type='AccountLock', subject_id=lock.id, subject_version=None,
            before=None, after={'status': lock.status.value, 'scope': lock.scope.value},
            reason=lock.reason, correlation_id=command.correlation_id,
        ))
        try:
            self._flush()
        except IntegrityError as error:
            raise AccountLockConflictError('active lock already exists') from error
        return lock

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError('clock requires timezone')
        return now.astimezone(UTC)


class ReleaseAccountLock:
    def __init__(self, repository: AccountLockRepository, authorization: AuthorizationService,
                 service: AccountLockService, *, flush: Callable[[], None],
                 clock: Callable[[], datetime] | None = None) -> None:
        self._repository = repository
        self._authorization = authorization
        self._service = service
        self._flush = flush
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(self, command: ReleaseAccountLockCommand) -> AccountLock:
        authorization = self._authorization.require(AuthorizationRequest(
            command.tenant_id, command.actor_id, PermissionCode('lock.manage'), command.company_id,
        ), at=self._now())
        lock = self._repository.get(command.tenant_id, command.lock_id)
        if lock is None or lock.company_id != command.company_id:
            raise PermissionError('access denied')
        outcome = self._service.release(
            lock, authorization=authorization, reason=command.reason,
            correlation_id=command.correlation_id, released_at=self._now(),
        )
        self._repository.save(outcome.lock)
        self._flush()
        return outcome.lock

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError('clock requires timezone')
        return now.astimezone(UTC)


class PersistedAccountLockGuard:
    '''Aplica exatamente a semântica de domínio sobre locks persistidos ativos.'''

    def __init__(self, repository: AccountLockRepository) -> None:
        self._repository = repository

    def validate(self, context: EffectContext) -> EffectValidation:
        return validate_effect(
            self._repository.list_active(context.tenant_id, context.company_id), context,
        )
