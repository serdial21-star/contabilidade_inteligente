'''Models ORM privados e imutáveis do domínio fiscal.'''

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from serdial21.bootstrap.database import Base, UTCDateTime


TABLE_OPTIONS = {
    'mysql_charset': 'utf8mb4',
    'mysql_collate': 'utf8mb4_unicode_ci',
}


class ImmutableFiscalRecordError(RuntimeError):
    '''Impede alteração ou exclusão de saída fiscal derivada.'''


class CanonicalRecordModel(Base):
    __tablename__ = 'canonical_records'
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'company_id', 'id',
            name='uq_canonical_records_scope_id',
        ),
        Index(
            'ux_canonical_records_scope_artifact_id',
            'tenant_id', 'company_id', 'artifact_id', 'id',
            unique=True,
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id'],
            ['companies.tenant_id', 'companies.id'],
            name='fk_canonical_records_tenant_company',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'artifact_id'],
            ['evidence_artifacts.tenant_id', 'evidence_artifacts.id'],
            name='fk_canonical_records_tenant_artifact',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'artifact_id', 'transformation_run_id'],
            [
                'transformation_runs.tenant_id',
                'transformation_runs.company_id',
                'transformation_runs.artifact_id',
                'transformation_runs.id',
            ],
            name='fk_canonical_records_scope_run',
        ),
        Index(
            'ix_canonical_records_external_identity',
            'tenant_id', 'company_id', 'record_type', 'external_identity',
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    artifact_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    transformation_run_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    record_type: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(100), nullable=False)
    external_identity: Mapped[str] = mapped_column(String(100), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    fact_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, server_default=func.current_timestamp()
    )


class FiscalDocumentModel(Base):
    __tablename__ = 'fiscal_documents'
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'company_id', 'id',
            name='uq_fiscal_documents_scope_id',
        ),
        UniqueConstraint(
            'tenant_id', 'company_id', 'access_key',
            name='uq_fiscal_documents_scope_access_key',
        ),
        UniqueConstraint(
            'tenant_id', 'company_id', 'canonical_record_id',
            name='uq_fiscal_documents_scope_canonical',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'artifact_id', 'canonical_record_id'],
            [
                'canonical_records.tenant_id',
                'canonical_records.company_id',
                'canonical_records.artifact_id',
                'canonical_records.id',
            ],
            name='fk_fiscal_documents_scope_canonical',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'artifact_id'],
            ['evidence_artifacts.tenant_id', 'evidence_artifacts.id'],
            name='fk_fiscal_documents_tenant_artifact',
        ),
        Index('ix_fiscal_documents_issued_at', 'tenant_id', 'company_id', 'issued_at'),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    canonical_record_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    artifact_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    access_key: Mapped[str] = mapped_column(String(44), nullable=False)
    model: Mapped[str] = mapped_column(String(2), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    series: Mapped[str | None] = mapped_column(String(10), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    operation_nature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issuer_tax_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    issuer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_tax_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    movement_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    products_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    freight_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    insurance_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    discount_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    other_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    tax_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    invoice_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    observed_status: Mapped[str] = mapped_column(String(32), nullable=False)
    protocol_status_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    protocol_status_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, server_default=func.current_timestamp()
    )


class FiscalDocumentItemModel(Base):
    __tablename__ = 'fiscal_document_items'
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'company_id', 'id',
            name='uq_fiscal_document_items_scope_id',
        ),
        UniqueConstraint(
            'tenant_id', 'company_id', 'fiscal_document_id', 'sequence',
            name='uq_fiscal_document_items_scope_sequence',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'fiscal_document_id'],
            ['fiscal_documents.tenant_id', 'fiscal_documents.company_id', 'fiscal_documents.id'],
            name='fk_fiscal_document_items_scope_document',
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fiscal_document_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ncm: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cfop: Mapped[str | None] = mapped_column(String(8), nullable=True)
    commercial_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    unit_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 10), nullable=True)
    gross_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    discount_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    other_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    included_in_total: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, server_default=func.current_timestamp()
    )


class TaxDetailModel(Base):
    __tablename__ = 'tax_details'
    __table_args__ = (
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'fiscal_document_item_id'],
            ['fiscal_document_items.tenant_id', 'fiscal_document_items.company_id', 'fiscal_document_items.id'],
            name='fk_tax_details_scope_item',
        ),
        Index(
            'ix_tax_details_scope_type',
            'tenant_id', 'company_id', 'tax_type',
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fiscal_document_item_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False)
    tax_status: Mapped[str | None] = mapped_column(String(10), nullable=True)
    calculation_base: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, server_default=func.current_timestamp()
    )


def _prevent_change(*_: object) -> None:
    raise ImmutableFiscalRecordError('registro fiscal derivado é imutável')


for immutable_model in (
    CanonicalRecordModel,
    FiscalDocumentModel,
    FiscalDocumentItemModel,
    TaxDetailModel,
):
    event.listen(immutable_model, 'before_update', _prevent_change)
    event.listen(immutable_model, 'before_delete', _prevent_change)
