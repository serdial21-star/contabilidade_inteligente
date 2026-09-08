from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKeyConstraint, Index, Integer, JSON, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from serdial21.bootstrap.database import Base, UTCDateTime


class AccountLockModel(Base):
    __tablename__ = 'account_locks'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'], name='fk_account_locks_tenant_company'),
        UniqueConstraint('tenant_id', 'company_id', 'scope_fingerprint', 'active_marker', name='uq_account_locks_active_scope'),
        Index('ix_account_locks_scope_status', 'tenant_id', 'company_id', 'status'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'},
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    operations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    account_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    group_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    module: Mapped[str | None] = mapped_column(String(100))
    competence: Mapped[date | None] = mapped_column(Date)
    exercise: Mapped[int | None] = mapped_column(Integer)
    released_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    release_reason: Mapped[str | None] = mapped_column(String(500))
    scope_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    active_marker: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, server_default=func.current_timestamp())
