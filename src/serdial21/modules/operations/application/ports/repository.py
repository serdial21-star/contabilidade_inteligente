'''Porta de leitura operacional, sempre escopada por tenant e empresa.'''

from typing import Protocol
from uuid import UUID

from serdial21.modules.audit.domain.entities import AuditEvent
from serdial21.modules.intake_documents.domain.entities import ImportBatch, ValidationIssue
from serdial21.modules.workflow.application.journey import Journey


class OperationalQueryRepository(Protocol):
    def get_batch(
        self, tenant_id: UUID, company_id: UUID, batch_id: UUID,
    ) -> ImportBatch | None: ...

    def batch_content_hash(
        self, tenant_id: UUID, company_id: UUID, batch_id: UUID,
    ) -> str | None: ...

    def list_journeys(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[Journey, ...]: ...

    def get_journey(
        self, tenant_id: UUID, company_id: UUID, journey_id: UUID,
    ) -> Journey | None: ...

    def list_issues(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[ValidationIssue, ...]: ...

    def list_audit_events(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[AuditEvent, ...]: ...
