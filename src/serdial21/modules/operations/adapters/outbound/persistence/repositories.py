'''Consultas SQLAlchemy escopadas para a borda operacional.'''

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.domain.entities import AuditEvent, AuditOrigin
from serdial21.modules.intake_documents.adapters.outbound.persistence.models import (
    ArtifactReceiptModel, EvidenceArtifactModel, ImportBatchModel, ValidationIssueModel,
)
from serdial21.modules.intake_documents.domain.entities import ImportBatch, ValidationIssue
from serdial21.modules.workflow.adapters.outbound.persistence.journeys import (
    JourneyCheckpointModel, SqlAlchemyJourneyRepository,
)
from serdial21.modules.workflow.application.journey import Journey


class SqlAlchemyOperationalQueryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._journeys = SqlAlchemyJourneyRepository(session)

    def get_batch(
        self, tenant_id: UUID, company_id: UUID, batch_id: UUID,
    ) -> ImportBatch | None:
        row = self._session.scalar(select(ImportBatchModel).where(
            ImportBatchModel.tenant_id == tenant_id,
            ImportBatchModel.company_id == company_id,
            ImportBatchModel.id == batch_id,
        ))
        return None if row is None else _batch(row)

    def batch_content_hash(
        self, tenant_id: UUID, company_id: UUID, batch_id: UUID,
    ) -> str | None:
        return self._session.scalar(
            select(EvidenceArtifactModel.content_hash)
            .join(ArtifactReceiptModel, (
                ArtifactReceiptModel.tenant_id == EvidenceArtifactModel.tenant_id
            ) & (
                ArtifactReceiptModel.artifact_id == EvidenceArtifactModel.id
            ))
            .where(
                ArtifactReceiptModel.tenant_id == tenant_id,
                ArtifactReceiptModel.company_id == company_id,
                ArtifactReceiptModel.batch_id == batch_id,
            ).order_by(ArtifactReceiptModel.received_at).limit(1)
        )

    def list_journeys(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[Journey, ...]:
        ids = tuple(self._session.scalars(
            select(JourneyCheckpointModel.journey_id)
            .where(
                JourneyCheckpointModel.tenant_id == tenant_id,
                JourneyCheckpointModel.company_id == company_id,
            )
            .group_by(JourneyCheckpointModel.journey_id)
            .order_by(func.max(JourneyCheckpointModel.created_at).desc())
            .limit(limit)
        ))
        return tuple(
            journey for journey_id in ids
            if (journey := self._journeys.get(
                tenant_id, company_id, journey_id,
            )) is not None
        )

    def get_journey(
        self, tenant_id: UUID, company_id: UUID, journey_id: UUID,
    ) -> Journey | None:
        return self._journeys.get(tenant_id, company_id, journey_id)

    def list_issues(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[ValidationIssue, ...]:
        rows = self._session.scalars(select(ValidationIssueModel).where(
            ValidationIssueModel.tenant_id == tenant_id,
            ValidationIssueModel.company_id == company_id,
        ).order_by(ValidationIssueModel.created_at.desc()).limit(limit))
        return tuple(_issue(row) for row in rows)

    def list_audit_events(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[AuditEvent, ...]:
        rows = self._session.scalars(select(AuditEventModel).where(
            AuditEventModel.tenant_id == tenant_id,
            AuditEventModel.company_id == company_id,
        ).order_by(AuditEventModel.occurred_at.desc()).limit(limit))
        return tuple(_audit(row) for row in rows)


def _batch(row: ImportBatchModel) -> ImportBatch:
    return ImportBatch(
        row.id, row.tenant_id, row.company_id, row.source,
        row.idempotency_key, row.status, row.total_items,
        row.received_items, row.duplicate_items, row.failed_items,
        row.started_at, row.completed_at, row.revision,
    )


def _issue(row: ValidationIssueModel) -> ValidationIssue:
    return ValidationIssue(
        row.id, row.tenant_id, row.company_id, row.transformation_run_id,
        row.code, row.severity, row.field_path, row.rule_reference,
        row.message, row.resolution_status, row.created_at,
    )


def _audit(row: AuditEventModel) -> AuditEvent:
    return AuditEvent(
        row.id, row.tenant_id, row.company_id, row.actor_id,
        AuditOrigin(row.origin), row.module, row.action, row.subject_type,
        row.subject_id, row.subject_version, row.before_state, row.after_state,
        row.reason, row.correlation_id, row.causation_id, row.occurred_at,
        row.integrity_hash,
    )
