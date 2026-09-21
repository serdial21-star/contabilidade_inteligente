'''Modelos persistentes tenant/company-aware da classificação por item.'''

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from serdial21.bootstrap.database import Base, UTCDateTime


OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}


class CompanyBusinessActivityModel(Base):
    __tablename__ = 'company_business_activities'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
                             name='fk_company_activities_company'),
        UniqueConstraint('tenant_id', 'company_id', 'id', name='uq_company_activities_scope_id'),
        UniqueConstraint('tenant_id', 'company_id', 'cnae_code', 'effective_from',
                         name='uq_company_activities_cnae_effective'),
        UniqueConstraint('tenant_id', 'company_id', 'active_primary_marker',
                         name='uq_company_activities_active_primary'),
        Index('ix_company_activities_scope_active', 'tenant_id', 'company_id', 'is_active'), OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    cnae_code: Mapped[str] = mapped_column(String(7), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active_primary_marker: Mapped[str | None] = mapped_column(String(16))
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column()


class CompanyAccountingProfileModel(Base):
    __tablename__ = 'company_accounting_profiles'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
                             name='fk_company_accounting_profiles_company'), OPTIONS,
    )
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    business_segment: Mapped[str] = mapped_column(String(32), nullable=False)
    keeps_inventory: Mapped[bool | None] = mapped_column(Boolean)
    manufactures_goods: Mapped[bool | None] = mapped_column(Boolean)
    resells_goods: Mapped[bool | None] = mapped_column(Boolean)
    provides_services: Mapped[bool | None] = mapped_column(Boolean)
    uses_cost_centers: Mapped[bool | None] = mapped_column(Boolean)
    uses_projects: Mapped[bool | None] = mapped_column(Boolean)
    controls_fixed_assets: Mapped[bool | None] = mapped_column(Boolean)
    capitalization_threshold: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    minimum_useful_life_months: Mapped[int | None] = mapped_column(Integer)
    capitalizes_freight_to_inventory: Mapped[bool | None] = mapped_column(Boolean)
    auto_proposal_confidence_threshold: Mapped[str] = mapped_column(String(16), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class CounterpartyModel(Base):
    __tablename__ = 'counterparties'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_counterparties_tenant_id'),
        UniqueConstraint('tenant_id', 'tax_id', name='uq_counterparties_tenant_tax'),
        Index('ix_counterparties_tenant_role', 'tenant_id', 'role'), OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    tax_id: Mapped[str] = mapped_column(String(32), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)


class CompanyItemProfileModel(Base):
    __tablename__ = 'company_item_profiles'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
                             name='fk_company_item_profiles_company'),
        ForeignKeyConstraint(['tenant_id', 'counterparty_id'], ['counterparties.tenant_id', 'counterparties.id'],
                             name='fk_company_item_profiles_counterparty'),
        UniqueConstraint('tenant_id', 'company_id', 'identity_hash', name='uq_company_item_profiles_identity'),
        Index('ix_company_item_profiles_product', 'tenant_id', 'company_id', 'counterparty_id',
              'supplier_product_code', 'gtin'), OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    counterparty_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    supplier_product_code: Mapped[str | None] = mapped_column(String(100))
    gtin: Mapped[str | None] = mapped_column(String(32))
    ncm: Mapped[str | None] = mapped_column(String(16))
    normalized_description: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    preferred_accounting_intent: Mapped[str | None] = mapped_column(String(64))
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    status: Mapped[str] = mapped_column(String(16), nullable=False)


class ItemClassificationModel(Base):
    __tablename__ = 'item_classifications'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'company_id', 'fiscal_document_item_id'],
                             ['fiscal_document_items.tenant_id', 'fiscal_document_items.company_id',
                              'fiscal_document_items.id'], name='fk_item_classifications_fiscal_item'),
        UniqueConstraint('tenant_id', 'company_id', 'id', name='uq_item_classifications_scope_id'),
        UniqueConstraint('tenant_id', 'company_id', 'fiscal_document_item_id', 'classification_version',
                         name='uq_item_classifications_item_version'),
        Index('ix_item_classifications_review', 'tenant_id', 'company_id', 'status', 'confidence_level'), OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fiscal_document_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fiscal_document_item_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    selected_intent: Mapped[str] = mapped_column(String(64), nullable=False)
    classification_category: Mapped[str | None] = mapped_column(String(100))
    confidence_level: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_version_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    classification_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, server_default=func.current_timestamp())


class ClassificationEvidenceModel(Base):
    __tablename__ = 'classification_evidence'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'company_id', 'classification_id'],
                             ['item_classifications.tenant_id', 'item_classifications.company_id',
                              'item_classifications.id'], name='fk_classification_evidence_result'), OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    classification_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    intent: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))


class ClassificationFeedbackModel(Base):
    __tablename__ = 'classification_feedback'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'company_id', 'classification_id'],
                             ['item_classifications.tenant_id', 'item_classifications.company_id',
                              'item_classifications.id'], name='fk_classification_feedback_result'),
        ForeignKeyConstraint(['actor_id'], ['users.id'], name='fk_classification_feedback_actor'),
        Index('ix_classification_feedback_item', 'tenant_id', 'company_id', 'classification_id'), OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    classification_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    original_intent: Mapped[str] = mapped_column(String(64), nullable=False)
    final_intent: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_type: Mapped[str] = mapped_column(String(16), nullable=False)
    apply_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
