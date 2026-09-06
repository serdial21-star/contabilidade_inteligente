"""Registros persistentes da jornada que ainda não produz efeito externo."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import ForeignKeyConstraint, Index, JSON, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from serdial21.bootstrap.database import Base, UTCDateTime

TABLE_OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}


class WorkflowCaseModel(Base):
    __tablename__ = 'workflow_cases'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'id', name='uq_workflow_cases_scope_id'),
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id']),
        Index('ix_workflow_cases_scope_correlation', 'tenant_id', 'company_id', 'correlation_id'),
        TABLE_OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, server_default=func.current_timestamp())


class WorkItemModel(Base):
    __tablename__ = 'workflow_work_items'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'id', name='uq_workflow_work_items_scope_id'),
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id']),
        ForeignKeyConstraint(['tenant_id', 'company_id', 'workflow_case_id'], ['workflow_cases.tenant_id', 'workflow_cases.company_id', 'workflow_cases.id']),
        Index('ix_workflow_work_items_scope_status', 'tenant_id', 'company_id', 'status'),
        Index('ix_workflow_work_items_correlation', 'tenant_id', 'correlation_id'),
        TABLE_OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    workflow_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    work_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_to_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, server_default=func.current_timestamp())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class ApprovalRequestModel(Base):
    __tablename__ = 'workflow_approval_requests'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'id', name='uq_workflow_approval_requests_scope_id'),
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id']),
        ForeignKeyConstraint(['tenant_id', 'company_id', 'workflow_case_id'], ['workflow_cases.tenant_id', 'workflow_cases.company_id', 'workflow_cases.id']),
        TABLE_OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    workflow_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    proposal_revision_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    proposal_revision_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_role: Mapped[str] = mapped_column(String(32), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, server_default=func.current_timestamp())


class AuthorizedEffectModel(Base):
    __tablename__ = 'authorized_effects'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'id', name='uq_authorized_effects_scope_id'),
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id']),
        ForeignKeyConstraint(['tenant_id', 'company_id', 'workflow_case_id'], ['workflow_cases.tenant_id', 'workflow_cases.company_id', 'workflow_cases.id']),
        ForeignKeyConstraint(['tenant_id', 'company_id', 'approval_request_id'], ['workflow_approval_requests.tenant_id', 'workflow_approval_requests.company_id', 'workflow_approval_requests.id']),
        Index('ix_authorized_effects_scope_status', 'tenant_id', 'company_id', 'authorization_status', 'execution_status'),
        TABLE_OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    workflow_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    approval_request_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    effect_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    authorized_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    authorization_status: Mapped[str] = mapped_column(String(32), nullable=False)
    authorized_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    authorized_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    execution_status: Mapped[str] = mapped_column(String(32), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, server_default=func.current_timestamp())


class PreHomologationExportBatchModel(Base):
    __tablename__ = 'pre_homologation_export_batches'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'id', name='uq_pre_homologation_export_batches_scope_id'),
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id']),
        ForeignKeyConstraint(['tenant_id', 'company_id', 'authorized_effect_id'], ['authorized_effects.tenant_id', 'authorized_effects.company_id', 'authorized_effects.id']),
        ForeignKeyConstraint(['tenant_id', 'company_id', 'fiscal_document_id'], ['fiscal_documents.tenant_id', 'fiscal_documents.company_id', 'fiscal_documents.id']),
        ForeignKeyConstraint(['tenant_id', 'company_id', 'canonical_record_id'], ['canonical_records.tenant_id', 'canonical_records.company_id', 'canonical_records.id']),
        ForeignKeyConstraint(['tenant_id', 'artifact_id'], ['evidence_artifacts.tenant_id', 'evidence_artifacts.id']),
        Index('ix_pre_homologation_export_batches_correlation', 'tenant_id', 'correlation_id'),
        TABLE_OPTIONS,
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    authorized_effect_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fiscal_document_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    canonical_record_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    artifact_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    connector_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    block_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, server_default=func.current_timestamp())
