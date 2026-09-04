'''Porta de persistência append-only e tenant-aware.'''

from typing import Protocol
from uuid import UUID

from serdial21.modules.audit.domain.entities import AuditEvent


class AuditRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...

    def get(self, tenant_id: UUID, event_id: UUID) -> AuditEvent | None: ...

    def list_by_correlation(
        self,
        tenant_id: UUID,
        correlation_id: UUID,
    ) -> list[AuditEvent]: ...

