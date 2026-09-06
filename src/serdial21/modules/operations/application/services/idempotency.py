'''Orquestrador que somente confirma o efeito junto do evento/outbox/inbox.'''

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from serdial21.modules.operations.application.ports.repository import OperationRepository
from serdial21.modules.operations.domain.entities import (
    CriticalOperation,
    DomainEvent,
    IdempotencyConflictError,
    IdempotencyStatus,
    InboxReceipt,
    OutboxMessage,
    OutboxStatus,
)


@dataclass(frozen=True, slots=True)
class CriticalCommand:
    tenant_id: UUID
    company_id: UUID
    consumer: str
    idempotency_key: str
    payload_hash: str
    operation: CriticalOperation
    subject_type: str
    correlation_id: UUID
    causation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class IdempotentResult:
    result_id: UUID
    reused: bool


class IdempotentOperationService:
    def __init__(self, repository: OperationRepository, *,
                 id_factory: Callable[[], UUID] = uuid4,
                 clock: Callable[[], datetime] | None = None) -> None:
        self._repository = repository
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(self, command: CriticalCommand,
                effect: Callable[[], UUID]) -> IdempotentResult:
        if not command.consumer.strip() or not command.idempotency_key.strip() or not command.payload_hash:
            raise ValueError('comando crítico exige consumidor, chave e hash')
        existing = self._repository.find_inbox_receipt(
            command.tenant_id, command.company_id, command.consumer, command.idempotency_key,
        )
        if existing is not None:
            if existing.payload_hash != command.payload_hash:
                raise IdempotencyConflictError()
            return IdempotentResult(existing.result_id, reused=True)
        result_id = effect()
        event = DomainEvent(
            self._id_factory(), command.tenant_id, command.company_id,
            f'{command.operation.value}.completed', 'v1', command.subject_type, result_id,
            command.payload_hash, command.correlation_id, command.causation_id, self._now(),
        )
        outbox = OutboxMessage(
            self._id_factory(), command.tenant_id, command.company_id, event.id,
            command.payload_hash, OutboxStatus.PENDING, 0,
        )
        receipt = InboxReceipt(
            self._id_factory(), command.tenant_id, command.company_id, command.consumer,
            command.idempotency_key, command.payload_hash, result_id, IdempotencyStatus.COMPLETED,
        )
        self._repository.commit_effect_with_messages(
            result_id=result_id, event=event, outbox=outbox, receipt=receipt,
        )
        return IdempotentResult(result_id, reused=False)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('evento exige timestamp com timezone')
        return value.astimezone(UTC)
