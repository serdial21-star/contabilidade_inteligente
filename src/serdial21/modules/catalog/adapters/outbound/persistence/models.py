'''Agregado persistente e imutável após publicação.'''

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Date, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, String,
    UniqueConstraint, Uuid, event, func, inspect,
)
from sqlalchemy.orm import Mapped, mapped_column

from serdial21.bootstrap.database import Base, UTCDateTime


TABLE_OPTIONS = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}


class ProductionCatalogModel(Base):
    __tablename__ = 'production_catalogs'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'id', name='uq_production_catalogs_scope_id'),
        UniqueConstraint('tenant_id', 'company_id', name='uq_production_catalogs_scope'),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
            name='fk_production_catalogs_tenant_company',
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, server_default=func.current_timestamp(),
    )


class ProductionCatalogVersionModel(Base):
    __tablename__ = 'production_catalog_versions'
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'company_id', 'id', name='uq_production_catalog_versions_scope_id',
        ),
        UniqueConstraint(
            'tenant_id', 'company_id', 'catalog_id', 'version_no',
            name='uq_production_catalog_versions_number',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id'], ['companies.tenant_id', 'companies.id'],
            name='fk_production_catalog_versions_tenant_company',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'catalog_id'],
            ['production_catalogs.tenant_id', 'production_catalogs.company_id', 'production_catalogs.id'],
            name='fk_production_catalog_versions_catalog',
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'company_id', 'supersedes_version_id'],
            ['production_catalog_versions.tenant_id', 'production_catalog_versions.company_id',
             'production_catalog_versions.id'],
            name='fk_production_catalog_versions_supersedes',
        ),
        Index(
            'ix_production_catalog_versions_active',
            'tenant_id', 'company_id', 'status', 'valid_from', 'valid_to',
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    catalog_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    supersedes_version_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('users.id'), nullable=False)
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey('users.id'))
    published_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


def _published_is_immutable(_: object, __: object, target: ProductionCatalogVersionModel) -> None:
    history = inspect(target).attrs.status.history
    previous = history.deleted[0] if history.deleted else target.status
    if previous == 'PUBLISHED':
        raise ValueError('versão publicada do catálogo é imutável')


def _versions_are_historical(_: object, __: object, target: ProductionCatalogVersionModel) -> None:
    raise ValueError('histórico do catálogo não pode ser removido')


event.listen(ProductionCatalogVersionModel, 'before_update', _published_is_immutable)
event.listen(ProductionCatalogVersionModel, 'before_delete', _versions_are_historical)
