"""Checkpoints append-only do coordenador, com hash e concorrência otimista."""
from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Any
from uuid import UUID, uuid4

from pydantic import TypeAdapter
from sqlalchemy import ForeignKeyConstraint, Index, JSON, String, UniqueConstraint, Uuid, event, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from serdial21.bootstrap.database import Base, UTCDateTime
from serdial21.modules.workflow.application.journey import Journey, JourneyConflictError

CODEC = TypeAdapter(Journey)


class JourneyCheckpointModel(Base):
    __tablename__ = 'nfe_journey_checkpoints'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'journey_id', 'version', name='uq_nfe_journey_version'),
        UniqueConstraint('tenant_id', 'company_id', 'idempotency_key', 'version', name='uq_nfe_journey_key_version'),
        UniqueConstraint('correlation_id', 'version', name='uq_nfe_journey_correlation_version'),
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id']),
        ForeignKeyConstraint(['tenant_id', 'company_id', 'fiscal_document_id'],
                             ['fiscal_documents.tenant_id', 'fiscal_documents.company_id', 'fiscal_documents.id']),
        Index('ix_nfe_journey_export', 'tenant_id', 'company_id', 'export_batch_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'},
    )
    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False)
    journey_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    fiscal_document_id: Mapped[UUID | None] = mapped_column(Uuid(), nullable=True)
    export_batch_id: Mapped[UUID | None] = mapped_column(Uuid(), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


def snapshot_hash(snapshot: dict[str, Any]) -> str:
    return sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@event.listens_for(JourneyCheckpointModel, 'before_update')
@event.listens_for(JourneyCheckpointModel, 'before_delete')
def immutable_checkpoint(*_: object) -> None:
    raise JourneyConflictError('checkpoint is immutable')


class SqlAlchemyJourneyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _latest(self, tenant_id: UUID, company_id: UUID, **filters: object) -> Journey | None:
        statement = select(JourneyCheckpointModel).filter_by(
            tenant_id=tenant_id, company_id=company_id, **filters,
        ).order_by(JourneyCheckpointModel.version.desc()).limit(1)
        model = self._session.scalar(statement.execution_options(populate_existing=True))
        if model is None:
            return None
        if snapshot_hash(model.snapshot) != model.snapshot_hash:
            raise JourneyConflictError('checkpoint integrity mismatch')
        journey = CODEC.validate_python(model.snapshot)
        if (journey.tenant_id, journey.company_id, journey.id, journey.version) != (
            model.tenant_id, model.company_id, model.journey_id, model.version,
        ):
            raise JourneyConflictError('checkpoint scope mismatch')
        return journey

    def find_by_key(self, tenant_id: UUID, company_id: UUID, key: str) -> Journey | None:
        return self._latest(tenant_id, company_id, idempotency_key=key)

    def get(self, tenant_id: UUID, company_id: UUID, journey_id: UUID) -> Journey | None:
        return self._latest(tenant_id, company_id, journey_id=journey_id)

    def find_by_export(self, tenant_id: UUID, company_id: UUID, batch_id: UUID) -> Journey | None:
        found = self._latest(tenant_id, company_id, export_batch_id=batch_id)
        # Sempre retorna o estado atual, inclusive depois de supersession.
        return self.get(tenant_id, company_id, found.id) if found else None

    def append(self, journey: Journey) -> None:
        current = self.get(journey.tenant_id, journey.company_id, journey.id)
        if journey.version != (current.version + 1 if current else 1):
            raise JourneyConflictError('stale journey version')
        snapshot = CODEC.dump_python(journey, mode='json')
        self._session.add(JourneyCheckpointModel(
            id=uuid4(), tenant_id=journey.tenant_id, company_id=journey.company_id,
            journey_id=journey.id, correlation_id=journey.correlation_id,
            idempotency_key=journey.idempotency_key, version=journey.version,
            fiscal_document_id=journey.imported.fiscal_document_id,
            export_batch_id=journey.batch.id if journey.batch else None,
            status=journey.status, snapshot=snapshot, snapshot_hash=snapshot_hash(snapshot),
            created_at=datetime.now(UTC),
        ))
        # A constraint da versão decide corridas entre sessões. IntegrityError
        # invalida a UoW; o chamador deve fazer rollback e reler antes de retry.
        self._session.flush()

