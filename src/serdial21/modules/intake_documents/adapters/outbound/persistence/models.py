'''Models ORM privados do intake documental.'''

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    event,
    func,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column

from serdial21.bootstrap.database import Base, UTCDateTime


class ImmutableDocumentError(RuntimeError):
    '''Impede sobrescrita ou exclusão de evidência histórica.'''


TABLE_OPTIONS = {
    'mysql_charset': 'utf8mb4',
    'mysql_collate': 'utf8mb4_unicode_ci',
}


class EvidenceArtifactModel(Base):
    __tablename__ = 'evidence_artifacts'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_evidence_artifacts_tenant_id'),
        UniqueConstraint(
            'tenant_id',
            'hash_algorithm',
            'content_hash',
            name='uq_evidence_artifacts_tenant_hash',
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('tenants.id'),
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    media_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )


class ImportBatchModel(Base):
    __tablename__ = 'import_batches'
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'company_id', 'id',
            name='uq_import_batches_scope_id',
        ),
        UniqueConstraint(
            'tenant_id', 'company_id', 'source', 'idempotency_key',
            name='uq_import_batches_scope_idempotency',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_import_batches_tenant_company',
        ),
        Index('ix_import_batches_scope_status', 'tenant_id', 'company_id', 'status'),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    received_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )


class ArtifactReceiptModel(Base):
    __tablename__ = 'artifact_receipts'
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'company_id', 'id',
            name='uq_artifact_receipts_scope_id',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_artifact_receipts_tenant_company',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'artifact_id'],
            ['evidence_artifacts.tenant_id', 'evidence_artifacts.id'],
            name='fk_artifact_receipts_tenant_artifact',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'batch_id'],
            ['import_batches.tenant_id', 'import_batches.company_id', 'import_batches.id'],
            name='fk_artifact_receipts_scope_batch',
        ),
        Index('ix_artifact_receipts_scope_time', 'tenant_id', 'company_id', 'received_at'),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    artifact_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    external_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )


class ImportItemModel(Base):
    __tablename__ = 'import_items'
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'company_id', 'batch_id', 'sequence',
            name='uq_import_items_batch_sequence',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'batch_id'],
            ['import_batches.tenant_id', 'import_batches.company_id', 'import_batches.id'],
            name='fk_import_items_scope_batch',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'receipt_id'],
            ['artifact_receipts.tenant_id', 'artifact_receipts.company_id', 'artifact_receipts.id'],
            name='fk_import_items_scope_receipt',
        ),
        Index('ix_import_items_scope_status', 'tenant_id', 'company_id', 'status'),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    receipt_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_subject_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_subject_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )


class TransformationRunModel(Base):
    __tablename__ = 'transformation_runs'
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'company_id', 'id',
            name='uq_transformation_runs_scope_id',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_transformation_runs_tenant_company',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'artifact_id'],
            ['evidence_artifacts.tenant_id', 'evidence_artifacts.id'],
            name='fk_transformation_runs_tenant_artifact',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'previous_run_id'],
            ['transformation_runs.tenant_id', 'transformation_runs.company_id', 'transformation_runs.id'],
            name='fk_transformation_runs_previous',
        ),
        Index(
            'ux_transformation_runs_scope_artifact_id',
            'tenant_id', 'company_id', 'artifact_id', 'id',
            unique=True,
        ),
        Index('ix_transformation_runs_scope_status', 'tenant_id', 'company_id', 'status'),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    artifact_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    previous_run_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    parser_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    output_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )


class ValidationIssueModel(Base):
    __tablename__ = 'validation_issues'
    __table_args__ = (
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'transformation_run_id'],
            ['transformation_runs.tenant_id', 'transformation_runs.company_id', 'transformation_runs.id'],
            name='fk_validation_issues_scope_run',
        ),
        Index('ix_validation_issues_scope_severity', 'tenant_id', 'company_id', 'severity'),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    transformation_run_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    field_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rule_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )


class LineageEdgeModel(Base):
    __tablename__ = 'lineage_edges'
    __table_args__ = (
        ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_lineage_edges_tenant_company',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'transformation_run_id'],
            ['transformation_runs.tenant_id', 'transformation_runs.company_id', 'transformation_runs.id'],
            name='fk_lineage_edges_scope_run',
        ),
        Index('ix_lineage_edges_source', 'tenant_id', 'company_id', 'source_type', 'source_id'),
        Index('ix_lineage_edges_target', 'tenant_id', 'company_id', 'target_type', 'target_id'),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    target_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transformation_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )


def _prevent_immutable_change(*_: object) -> None:
    raise ImmutableDocumentError('registro documental imutável')


for immutable_model in (
    EvidenceArtifactModel,
    ArtifactReceiptModel,
    LineageEdgeModel,
):
    event.listen(immutable_model, 'before_update', _prevent_immutable_change)
    event.listen(immutable_model, 'before_delete', _prevent_immutable_change)

for append_oriented_model in (ImportItemModel, ValidationIssueModel):
    event.listen(append_oriented_model, 'before_delete', _prevent_immutable_change)


@event.listens_for(TransformationRunModel, 'before_update')
def _prevent_completed_run_update(
    _: object,
    __: object,
    target: TransformationRunModel,
) -> None:
    history = inspect(target).attrs.status.history
    previous_status = history.deleted[0] if history.deleted else target.status
    if previous_status in {'COMPLETED', 'FAILED'}:
        raise ImmutableDocumentError('transformação terminal é imutável')


@event.listens_for(TransformationRunModel, 'before_delete')
def _prevent_completed_run_delete(
    _: object,
    __: object,
    target: TransformationRunModel,
) -> None:
    if target.status in {'COMPLETED', 'FAILED'}:
        raise ImmutableDocumentError('transformação terminal é imutável')
