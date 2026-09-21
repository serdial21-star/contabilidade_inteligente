'''Persistência scoped para classificação contábil por item.'''

from datetime import datetime
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from serdial21.modules.accounting.adapters.outbound.persistence.models import (
    ClassificationEvidenceModel, ClassificationFeedbackModel,
    CompanyAccountingProfileModel, CompanyItemProfileModel, ItemClassificationModel,
)
from serdial21.modules.accounting.application.ports.repository import ClassificationRecord
from serdial21.modules.accounting.domain.classification import (
    ApprovedItemHistory, ClassificationEvidence, CompanyAccountingProfile,
    ItemClassification, ItemEvidence, normalize_description,
)
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.models import (
    FiscalDocumentItemModel, FiscalDocumentModel,
)


class SqlAlchemyAccountingClassificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_profile(self, tenant_id: UUID, company_id: UUID) -> CompanyAccountingProfile | None:
        model = self._session.get(CompanyAccountingProfileModel, (tenant_id, company_id))
        if model is None:
            return None
        return CompanyAccountingProfile(
            model.tenant_id, model.company_id, model.business_segment,
            model.keeps_inventory, model.manufactures_goods, model.resells_goods,
            model.provides_services, model.uses_cost_centers, model.uses_projects,
            model.controls_fixed_assets, model.capitalization_threshold,
            model.minimum_useful_life_months, model.capitalizes_freight_to_inventory,
            model.auto_proposal_confidence_threshold,
        )

    def get_history(self, item: ItemEvidence) -> ApprovedItemHistory | None:
        conditions = []
        if item.gtin:
            conditions.append(CompanyItemProfileModel.gtin == item.gtin)
        if item.supplier_product_code:
            conditions.append(
                CompanyItemProfileModel.supplier_product_code == item.supplier_product_code,
            )
        if not conditions:
            return None
        model = self._session.scalar(select(CompanyItemProfileModel).where(
            CompanyItemProfileModel.tenant_id == item.tenant_id,
            CompanyItemProfileModel.company_id == item.company_id,
            CompanyItemProfileModel.status == 'ACTIVE',
            CompanyItemProfileModel.preferred_accounting_intent.is_not(None),
            or_(*conditions),
        ).order_by(CompanyItemProfileModel.approved_count.desc()).limit(1))
        if model is None or model.preferred_accounting_intent is None:
            return None
        return ApprovedItemHistory(
            model.preferred_accounting_intent, True, model.approved_count,
            None, model.supplier_product_code, model.gtin,
        )

    def add_classification(self, item: ItemEvidence, result: ItemClassification,
                           *, created_at: datetime) -> ClassificationRecord:
        latest = self._session.scalar(select(ItemClassificationModel).where(
            ItemClassificationModel.tenant_id == item.tenant_id,
            ItemClassificationModel.company_id == item.company_id,
            ItemClassificationModel.fiscal_document_item_id == item.fiscal_item_id,
        ).order_by(ItemClassificationModel.classification_version.desc()).limit(1))
        if latest is not None and _same_result(latest, result):
            return self._record(latest)
        version = 1 if latest is None else latest.classification_version + 1
        model = ItemClassificationModel(
            id=uuid4(), tenant_id=item.tenant_id, company_id=item.company_id,
            fiscal_document_id=item.fiscal_document_id,
            fiscal_document_item_id=item.fiscal_item_id,
            selected_intent=result.intent, classification_category=result.category,
            confidence_level=result.confidence_level, status=result.status,
            rule_version_id=result.rule_version_id, classification_version=version,
            created_at=created_at,
        )
        self._session.add(model)
        self._session.flush()
        for evidence in result.evidence:
            self._session.add(ClassificationEvidenceModel(
                id=uuid4(), tenant_id=item.tenant_id, company_id=item.company_id,
                classification_id=model.id, kind=evidence.kind, intent=evidence.intent,
                weight=evidence.weight, explanation=evidence.explanation,
                reference_id=evidence.reference_id,
            ))
        return ClassificationRecord(
            model.id, item.tenant_id, item.company_id, item.fiscal_document_id,
            item.fiscal_item_id, result, version, created_at,
        )

    def get_classification(self, tenant_id: UUID, company_id: UUID,
                           classification_id: UUID) -> ClassificationRecord | None:
        model = self._session.scalar(select(ItemClassificationModel).where(
            ItemClassificationModel.tenant_id == tenant_id,
            ItemClassificationModel.company_id == company_id,
            ItemClassificationModel.id == classification_id,
        ))
        return None if model is None else self._record(model)

    def list_pending(self, tenant_id: UUID, company_id: UUID, *, offset: int,
                     limit: int) -> tuple[tuple[ClassificationRecord, ...], int]:
        latest_version = select(
            ItemClassificationModel.fiscal_document_item_id,
            func.max(ItemClassificationModel.classification_version).label('max_version'),
        ).where(
            ItemClassificationModel.tenant_id == tenant_id,
            ItemClassificationModel.company_id == company_id,
        ).group_by(ItemClassificationModel.fiscal_document_item_id).subquery()
        base = select(ItemClassificationModel).join(latest_version, (
            ItemClassificationModel.fiscal_document_item_id
            == latest_version.c.fiscal_document_item_id
        ) & (
            ItemClassificationModel.classification_version == latest_version.c.max_version
        )).where(
            ItemClassificationModel.tenant_id == tenant_id,
            ItemClassificationModel.company_id == company_id,
            ItemClassificationModel.status.in_(('REVIEW_REQUIRED', 'CONFLICTING_EVIDENCE')),
        )
        total = self._session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self._session.scalars(base.order_by(
            ItemClassificationModel.created_at.desc(),
        ).offset(offset).limit(limit))
        return tuple(self._record(model) for model in rows), total

    def get_item(self, tenant_id: UUID, company_id: UUID,
                 fiscal_item_id: UUID) -> ItemEvidence | None:
        row = self._session.execute(
            select(FiscalDocumentItemModel, FiscalDocumentModel.issuer_tax_id)
            .join(FiscalDocumentModel, (
                FiscalDocumentModel.tenant_id == FiscalDocumentItemModel.tenant_id
            ) & (
                FiscalDocumentModel.company_id == FiscalDocumentItemModel.company_id
            ) & (
                FiscalDocumentModel.id == FiscalDocumentItemModel.fiscal_document_id
            ))
            .where(
                FiscalDocumentItemModel.tenant_id == tenant_id,
                FiscalDocumentItemModel.company_id == company_id,
                FiscalDocumentItemModel.id == fiscal_item_id,
            )
        ).first()
        if row is None:
            return None
        item, supplier_tax_id = row
        if item.gross_total is None or item.description is None:
            return None
        return ItemEvidence(
            item.tenant_id, item.company_id, item.fiscal_document_id, item.id,
            supplier_tax_id, item.product_code, item.gtin, item.description,
            item.ncm, item.cfop, None, item.gross_total,
        )

    def add_feedback(self, record: ClassificationRecord, *, original_intent: str,
                     final_intent: str, decision_type: str, apply_scope: str,
                     actor_id: UUID, decided_at: datetime) -> None:
        self._session.add(ClassificationFeedbackModel(
            id=uuid4(), tenant_id=record.tenant_id, company_id=record.company_id,
            classification_id=record.id, original_intent=original_intent,
            final_intent=final_intent, decision_type=decision_type,
            apply_scope=apply_scope, actor_id=actor_id, decided_at=decided_at,
        ))

    def feedback_exists(self, record: ClassificationRecord, *, final_intent: str,
                        apply_scope: str, actor_id: UUID) -> bool:
        return self._session.scalar(select(ClassificationFeedbackModel.id).where(
            ClassificationFeedbackModel.tenant_id == record.tenant_id,
            ClassificationFeedbackModel.company_id == record.company_id,
            ClassificationFeedbackModel.classification_id == record.id,
            ClassificationFeedbackModel.final_intent == final_intent,
            ClassificationFeedbackModel.apply_scope == apply_scope,
            ClassificationFeedbackModel.actor_id == actor_id,
        ).limit(1)) is not None

    def save_reusable_history(self, item: ItemEvidence, *, intent: str,
                              used_at: datetime) -> None:
        identity_hash = _identity_hash(item)
        model = self._session.scalar(select(CompanyItemProfileModel).where(
            CompanyItemProfileModel.tenant_id == item.tenant_id,
            CompanyItemProfileModel.company_id == item.company_id,
            CompanyItemProfileModel.identity_hash == identity_hash,
        ))
        if model is None:
            model = CompanyItemProfileModel(
                id=uuid4(), tenant_id=item.tenant_id, company_id=item.company_id,
                counterparty_id=None, supplier_product_code=item.supplier_product_code,
                gtin=item.gtin, ncm=item.ncm,
                normalized_description=normalize_description(item.description),
                identity_hash=identity_hash, preferred_accounting_intent=intent,
                occurrence_count=1, approved_count=1, last_used_at=used_at,
                status='ACTIVE',
            )
            self._session.add(model)
            return
        model.preferred_accounting_intent = intent
        model.occurrence_count += 1
        model.approved_count += 1
        model.last_used_at = used_at
        model.status = 'ACTIVE'

    def flush(self) -> None:
        self._session.flush()

    def _record(self, model: ItemClassificationModel) -> ClassificationRecord:
        evidence = tuple(ClassificationEvidence(
            item.kind, item.intent, item.weight, item.explanation, item.reference_id,
        ) for item in self._session.scalars(select(ClassificationEvidenceModel).where(
            ClassificationEvidenceModel.tenant_id == model.tenant_id,
            ClassificationEvidenceModel.company_id == model.company_id,
            ClassificationEvidenceModel.classification_id == model.id,
        ).order_by(ClassificationEvidenceModel.id)))
        result = ItemClassification(
            model.selected_intent, model.classification_category,
            model.confidence_level, model.status, evidence, model.rule_version_id,
        )
        return ClassificationRecord(
            model.id, model.tenant_id, model.company_id, model.fiscal_document_id,
            model.fiscal_document_item_id, result, model.classification_version,
            model.created_at,
        )


def _same_result(model: ItemClassificationModel, result: ItemClassification) -> bool:
    return (
        model.selected_intent == result.intent
        and model.classification_category == result.category
        and model.confidence_level == result.confidence_level
        and model.status == result.status
        and model.rule_version_id == result.rule_version_id
    )


def _identity_hash(item: ItemEvidence) -> str:
    value = '|'.join((
        item.supplier_tax_id or '', item.supplier_product_code or '', item.gtin or '',
        item.ncm or '', normalize_description(item.description),
    ))
    return sha256(value.encode()).hexdigest()
