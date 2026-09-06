'''Porta tenant-aware da persistência fiscal canônica.'''

from typing import Protocol
from uuid import UUID

from serdial21.modules.fiscal_documents.domain.entities import (
    CanonicalRecord,
    FiscalDocument,
    FiscalDocumentItem,
    TaxDetail,
)


class FiscalDocumentRepository(Protocol):
    def find_by_access_key(
        self,
        tenant_id: UUID,
        company_id: UUID,
        access_key: str,
    ) -> tuple[FiscalDocument, CanonicalRecord] | None: ...

    def add_document(
        self,
        canonical: CanonicalRecord,
        document: FiscalDocument,
        items: tuple[FiscalDocumentItem, ...],
        taxes: tuple[TaxDetail, ...],
    ) -> None: ...
