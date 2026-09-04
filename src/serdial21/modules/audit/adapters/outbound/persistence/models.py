'''Model ORM append-only da auditoria.'''

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
    String,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from serdial21.bootstrap.database import Base, UTCDateTime
from serdial21.modules.audit.domain.entities import AuditEventImmutableError


class AuditEventModel(Base):
    __tablename__ = 'audit_events'
    __table_args__ = (
        ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_audit_events_tenant_company',
        ),
        CheckConstraint(
            'origin IN (' + ','.join(chr(39) + value + chr(39) for value in (
                'HUMAN', 'AI', 'RULE_ENGINE', 'IMPORT', 'API',
                'INTEGRATION', 'AUTOMATION',
            )) + ')',
            name='audit_origin',
        ),
        Index('ix_audit_events_tenant_occurred_at', 'tenant_id', 'occurred_at'),
        Index('ix_audit_events_tenant_company_time', 'tenant_id', 'company_id', 'occurred_at'),
        Index('ix_audit_events_tenant_correlation', 'tenant_id', 'correlation_id'),
        Index('ix_audit_events_tenant_subject', 'tenant_id', 'subject_type', 'subject_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'},
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('tenants.id'),
        nullable=False,
    )
    company_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    origin: Mapped[str] = mapped_column(String(32), nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_version: Mapped[int | None] = mapped_column(nullable=True)
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    causation_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    integrity_hash: Mapped[str] = mapped_column(String(64), nullable=False)


@event.listens_for(AuditEventModel, 'before_update')
def _prevent_audit_update(*_: object) -> None:
    raise AuditEventImmutableError('evento de auditoria é imutável')


@event.listens_for(AuditEventModel, 'before_delete')
def _prevent_audit_delete(*_: object) -> None:
    raise AuditEventImmutableError('evento de auditoria é append-only')
