'''A implementação deve gravar efeito, evento, outbox e inbox no mesmo commit.'''

from typing import Protocol
from uuid import UUID

from serdial21.modules.operations.domain.entities import DomainEvent, InboxReceipt, OutboxMessage


class OperationRepository(Protocol):
    def find_inbox_receipt(self, tenant_id: UUID, company_id: UUID, consumer: str,
                           idempotency_key: str) -> InboxReceipt | None: ...

    def commit_effect_with_messages(self, *, result_id: UUID, event: DomainEvent,
                                    outbox: OutboxMessage, receipt: InboxReceipt) -> None: ...
