'''Porta tenant/company-aware para classificação contábil por item.'''

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from serdial21.modules.accounting.domain.classification import (
    ApprovedItemHistory, CompanyAccountingProfile, ItemClassification, ItemEvidence,
)


@dataclass(frozen=True, slots=True)
class ClassificationRecord:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    fiscal_document_id: UUID
    fiscal_item_id: UUID
    classification: ItemClassification
    version: int
    created_at: datetime


class AccountingClassificationRepository(Protocol):
    def get_profile(self, tenant_id: UUID, company_id: UUID) -> CompanyAccountingProfile | None: ...
    def get_history(self, item: ItemEvidence) -> ApprovedItemHistory | None: ...
    def add_classification(self, item: ItemEvidence, result: ItemClassification,
                           *, created_at: datetime) -> ClassificationRecord: ...
    def get_classification(self, tenant_id: UUID, company_id: UUID,
                           classification_id: UUID) -> ClassificationRecord | None: ...
    def list_pending(self, tenant_id: UUID, company_id: UUID, *, offset: int,
                     limit: int) -> tuple[tuple[ClassificationRecord, ...], int]: ...
    def get_item(self, tenant_id: UUID, company_id: UUID,
                 fiscal_item_id: UUID) -> ItemEvidence | None: ...
    def add_feedback(self, record: ClassificationRecord, *, original_intent: str,
                     final_intent: str, decision_type: str, apply_scope: str,
                     actor_id: UUID, decided_at: datetime) -> None: ...
    def feedback_exists(self, record: ClassificationRecord, *, final_intent: str,
                        apply_scope: str, actor_id: UUID) -> bool: ...
    def save_reusable_history(self, item: ItemEvidence, *, intent: str,
                              used_at: datetime) -> None: ...
    def flush(self) -> None: ...
