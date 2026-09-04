'''Repositório SQLAlchemy tenant-aware da auditoria.'''

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from serdial21.modules.audit.adapters.outbound.persistence.models import (
    AuditEventModel,
)
from serdial21.modules.audit.domain.entities import AuditEvent, AuditOrigin


class SqlAlchemyAuditRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, audit_event: AuditEvent) -> None:
        self._session.add(
            AuditEventModel(
                id=audit_event.id,
                tenant_id=audit_event.tenant_id,
                company_id=audit_event.company_id,
                actor_id=audit_event.actor_id,
                origin=audit_event.origin.value,
                module=audit_event.module,
                action=audit_event.action,
                subject_type=audit_event.subject_type,
                subject_id=audit_event.subject_id,
                subject_version=audit_event.subject_version,
                before_state=audit_event.before,
                after_state=audit_event.after,
                reason=audit_event.reason,
                correlation_id=audit_event.correlation_id,
                causation_id=audit_event.causation_id,
                occurred_at=audit_event.occurred_at,
                integrity_hash=audit_event.integrity_hash,
            )
        )

    def get(self, tenant_id: UUID, event_id: UUID) -> AuditEvent | None:
        statement = select(AuditEventModel).where(
            AuditEventModel.tenant_id == tenant_id,
            AuditEventModel.id == event_id,
        )
        model = self._session.scalar(statement)
        return None if model is None else _to_domain(model)

    def list_by_correlation(
        self,
        tenant_id: UUID,
        correlation_id: UUID,
    ) -> list[AuditEvent]:
        statement = (
            select(AuditEventModel)
            .where(
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.correlation_id == correlation_id,
            )
            .order_by(AuditEventModel.occurred_at, AuditEventModel.id)
        )
        return [_to_domain(model) for model in self._session.scalars(statement)]


def _to_domain(model: AuditEventModel) -> AuditEvent:
    return AuditEvent(
        id=model.id,
        tenant_id=model.tenant_id,
        company_id=model.company_id,
        actor_id=model.actor_id,
        origin=AuditOrigin(model.origin),
        module=model.module,
        action=model.action,
        subject_type=model.subject_type,
        subject_id=model.subject_id,
        subject_version=model.subject_version,
        before=model.before_state,
        after=model.after_state,
        reason=model.reason,
        correlation_id=model.correlation_id,
        causation_id=model.causation_id,
        occurred_at=model.occurred_at,
        integrity_hash=model.integrity_hash,
    )
