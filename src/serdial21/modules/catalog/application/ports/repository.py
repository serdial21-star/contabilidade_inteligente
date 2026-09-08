'''Porta de persistência do agregado de catálogo.'''

from datetime import date, datetime
from typing import Any, Protocol
from uuid import UUID

from serdial21.modules.catalog.domain.entities import CatalogVersion


class CatalogRepository(Protocol):
    def add_draft(
        self, tenant_id: UUID, company_id: UUID, name: str, version_no: int,
        content: dict[str, Any], content_hash: str, actor_id: UUID,
        now: datetime, valid_from: date, valid_to: date | None,
        *, catalog_id: UUID | None = None,
        supersedes_version_id: UUID | None = None,
    ) -> CatalogVersion: ...

    def get_for_update(
        self, tenant_id: UUID, company_id: UUID, version_id: UUID,
    ) -> CatalogVersion | None: ...

    def content(self, version_id: UUID) -> dict[str, Any]: ...

    def transition(
        self, version_id: UUID, expected_status: str, status: str,
        content: dict[str, Any], content_hash: str, actor_id: UUID,
        now: datetime,
    ) -> CatalogVersion: ...
