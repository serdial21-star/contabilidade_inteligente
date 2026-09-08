from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Boolean, ForeignKeyConstraint, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from serdial21.bootstrap.database import Base, UTCDateTime

OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
class RetentionPolicyModel(Base):
    __tablename__ = 'retention_policies'; __table_args__ = (ForeignKeyConstraint(['tenant_id'], ['tenants.id']), Index('ix_retention_policies_category', 'tenant_id', 'data_category'), OPTIONS)
    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, default=uuid4); tenant_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False)
    data_category: Mapped[str] = mapped_column(String(100), nullable=False); retention_days: Mapped[int | None] = mapped_column(Integer)
    retention_trigger: Mapped[str] = mapped_column(String(100), nullable=False); legal_basis_status: Mapped[str] = mapped_column(String(32), nullable=False)
    destruction_mode: Mapped[str] = mapped_column(String(64), nullable=False); approval_status: Mapped[str] = mapped_column(String(32), nullable=False)
    exceptions: Mapped[str | None] = mapped_column(String(500)); legal_hold_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False)
class LegalHoldModel(Base):
    __tablename__ = 'legal_holds'; __table_args__ = (ForeignKeyConstraint(['tenant_id','company_id'], ['companies.tenant_id','companies.id']), Index('ix_legal_holds_active', 'tenant_id','company_id','resource_type','resource_id','status'), OPTIONS)
    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True); tenant_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False); company_id: Mapped[UUID | None] = mapped_column(Uuid())
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False); resource_id: Mapped[UUID | None] = mapped_column(Uuid()); reason_reference: Mapped[str] = mapped_column(String(500), nullable=False); status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False); created_by: Mapped[UUID] = mapped_column(Uuid(), nullable=False); released_at: Mapped[datetime | None] = mapped_column(UTCDateTime()); released_by: Mapped[UUID | None] = mapped_column(Uuid())
class DataSubjectRequestModel(Base):
    __tablename__ = 'data_subject_requests'; __table_args__ = (ForeignKeyConstraint(['tenant_id','company_id'], ['companies.tenant_id','companies.id']), Index('ix_dsr_scope_status','tenant_id','company_id','status'), OPTIONS)
    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True); tenant_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False); company_id: Mapped[UUID | None] = mapped_column(Uuid())
    subject_reference_hash: Mapped[str] = mapped_column(String(64), nullable=False); status: Mapped[str] = mapped_column(String(32), nullable=False); created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False); created_by: Mapped[UUID] = mapped_column(Uuid(), nullable=False); verified_by: Mapped[UUID | None] = mapped_column(Uuid()); completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
