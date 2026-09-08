'''Persistência tenant-aware e implementação real de JourneyCatalog.'''

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from serdial21.modules.catalog.adapters.outbound.persistence.models import (
    ProductionCatalogModel, ProductionCatalogVersionModel,
)
from serdial21.modules.catalog.domain.entities import CatalogConflictError, CatalogVersion
from serdial21.modules.catalog.snapshot import preparation_plan, snapshot_hash
from serdial21.modules.locks.adapters.outbound.persistence.repositories import (
    SQLAlchemyAccountLockRepository,
)
from serdial21.modules.locks.domain.entities import AccountLock
from serdial21.modules.workflow.application.journey import PreparationPlan


class SqlAlchemyProductionCatalogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_draft(
        self, tenant_id: UUID, company_id: UUID, name: str, version_no: int,
        content: dict[str, Any], content_hash: str, actor_id: UUID,
        now: datetime, valid_from: date, valid_to: date | None,
        *, catalog_id: UUID | None = None,
        supersedes_version_id: UUID | None = None,
    ) -> CatalogVersion:
        if catalog_id is None:
            catalog_id = uuid4()
            self._session.add(ProductionCatalogModel(
                id=catalog_id, tenant_id=tenant_id, company_id=company_id,
                name=name, created_at=now,
            ))
            self._session.flush()
        else:
            root = self._session.scalar(select(ProductionCatalogModel).where(
                ProductionCatalogModel.tenant_id == tenant_id,
                ProductionCatalogModel.company_id == company_id,
                ProductionCatalogModel.id == catalog_id,
            ).with_for_update())
            if root is None or root.name != name:
                raise CatalogConflictError('catálogo raiz inválido')
        model = ProductionCatalogVersionModel(
            id=uuid4(), tenant_id=tenant_id, company_id=company_id,
            catalog_id=catalog_id, supersedes_version_id=supersedes_version_id,
            version_no=version_no, status='DRAFT', valid_from=valid_from,
            valid_to=valid_to, content=content, content_hash=content_hash,
            created_by=actor_id, created_at=now,
        )
        self._session.add(model)
        self._session.flush()
        return _domain(model)

    def get_for_update(
        self, tenant_id: UUID, company_id: UUID, version_id: UUID,
    ) -> CatalogVersion | None:
        model = self._session.scalar(select(ProductionCatalogVersionModel).where(
            ProductionCatalogVersionModel.tenant_id == tenant_id,
            ProductionCatalogVersionModel.company_id == company_id,
            ProductionCatalogVersionModel.id == version_id,
        ).with_for_update())
        return _domain(model) if model else None

    def content(self, version_id: UUID) -> dict[str, Any]:
        model = self._session.get(ProductionCatalogVersionModel, version_id)
        if model is None:
            raise CatalogConflictError('versão do catálogo indisponível')
        return model.content

    def transition(
        self, version_id: UUID, expected_status: str, status: str,
        content: dict[str, Any], content_hash: str, actor_id: UUID,
        now: datetime,
    ) -> CatalogVersion:
        model = self._session.scalar(select(ProductionCatalogVersionModel).where(
            ProductionCatalogVersionModel.id == version_id,
        ).with_for_update())
        if model is None or model.status != expected_status:
            raise CatalogConflictError('estado concorrente do catálogo')
        model.status = status
        model.content = content
        model.content_hash = content_hash
        if status == 'PUBLISHED':
            model.reviewed_by = actor_id
            model.published_by = actor_id
            model.reviewed_at = now
            model.published_at = now
        self._session.flush()
        return _domain(model)


class SqlAlchemyJourneyCatalog:
    '''Seleciona somente snapshot publicado, vigente e íntegro.'''

    def __init__(self, session: Session) -> None:
        self._session = session
        self._locks = SQLAlchemyAccountLockRepository(session)

    def preparation(
        self, tenant_id: UUID, company_id: UUID, at: date | None = None,
    ) -> PreparationPlan | None:
        effective = at or date.today()
        rows = list(self._session.scalars(
            select(ProductionCatalogVersionModel).where(
                ProductionCatalogVersionModel.tenant_id == tenant_id,
                ProductionCatalogVersionModel.company_id == company_id,
                ProductionCatalogVersionModel.status == 'PUBLISHED',
                ProductionCatalogVersionModel.valid_from <= effective,
                or_(
                    ProductionCatalogVersionModel.valid_to.is_(None),
                    ProductionCatalogVersionModel.valid_to >= effective,
                ),
            ).order_by(
                ProductionCatalogVersionModel.version_no.desc(),
            ).limit(1)
        ))
        if not rows:
            return None
        model = rows[0]
        if snapshot_hash(model.content) != model.content_hash:
            raise CatalogConflictError('integridade do catálogo inválida')
        return preparation_plan(model.content, tenant_id, company_id)

    def locks(self, tenant_id: UUID, company_id: UUID) -> tuple[AccountLock, ...]:
        return self._locks.list_active(tenant_id, company_id)


def _domain(model: ProductionCatalogVersionModel) -> CatalogVersion:
    return CatalogVersion(
        model.id, model.tenant_id, model.company_id, model.catalog_id,
        model.supersedes_version_id, model.version_no, model.status,
        model.valid_from, model.valid_to, model.content_hash, model.created_by,
        model.reviewed_by, model.published_by, model.created_at,
        model.reviewed_at, model.published_at,
    )

