'''Consultas SQLAlchemy escopadas para a borda operacional.'''

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, UTC
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session

from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.domain.entities import AuditEvent, AuditOrigin
from serdial21.modules.intake_documents.adapters.outbound.persistence.models import (
    ArtifactReceiptModel, EvidenceArtifactModel, ImportBatchModel, ImportItemModel,
    TransformationRunModel, ValidationIssueModel,
)
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyModel, TenantMembershipModel, UserModel,
)
from serdial21.modules.banking.adapters.outbound.persistence.models import (
    BankAccountModel, BankStatementModel, BankTransactionModel,
)
from serdial21.modules.catalog.adapters.outbound.persistence.models import ProductionCatalogVersionModel
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.models import (
    FiscalDocumentItemModel, FiscalDocumentModel, TaxDetailModel,
)
from serdial21.modules.intake_documents.domain.entities import ImportBatch, ValidationIssue
from serdial21.modules.locks.adapters.outbound.persistence.models import AccountLockModel
from serdial21.modules.locks.domain.entities import AccountLock, EffectOperation, LockScope, LockStatus
from serdial21.modules.catalog.snapshot import snapshot_hash
from serdial21.modules.workflow.adapters.outbound.persistence.journeys import (
    JourneyCheckpointModel, SqlAlchemyJourneyRepository,
)
from serdial21.modules.workflow.application.journey import Journey


@dataclass(frozen=True, slots=True)
class SqlCompanyRecord:
    id: UUID
    legal_name: str
    trade_name: str | None
    tax_identifier: str
    status: str
    timezone: str
    currency_code: str


@dataclass(frozen=True, slots=True)
class SqlDocumentRecord:
    id: UUID
    company_id: UUID
    batch_id: UUID
    artifact_id: UUID
    filename: str
    media_type: str
    size_bytes: int
    source: str
    channel: str
    receipt_result: str
    processing_status: str
    error_code: str | None
    received_at: datetime


@dataclass(frozen=True, slots=True)
class SqlFiscalRecord:
    id: UUID
    company_id: UUID
    artifact_id: UUID
    access_key: str
    model: str
    schema_version: str
    series: str | None
    document_number: str | None
    operation_nature: str | None
    issuer_tax_id: str | None
    issuer_name: str | None
    recipient_tax_id: str | None
    recipient_name: str | None
    issued_at: datetime | None
    movement_at: datetime | None
    products_total: Decimal | None
    freight_total: Decimal | None
    insurance_total: Decimal | None
    discount_total: Decimal | None
    other_total: Decimal | None
    tax_total: Decimal | None
    invoice_total: Decimal | None
    observed_status: str
    protocol_status_code: str | None
    protocol_status_reason: str | None
    created_at: datetime
    receipt_id: UUID | None


@dataclass(frozen=True, slots=True)
class SqlFiscalItemRecord:
    id: UUID
    sequence: int
    product_code: str | None
    description: str | None
    ncm: str | None
    cfop: str | None
    commercial_unit: str | None
    quantity: Decimal | None
    unit_value: Decimal | None
    gross_total: Decimal | None
    discount_total: Decimal | None
    other_total: Decimal | None
    included_in_total: bool | None


@dataclass(frozen=True, slots=True)
class SqlBankStatementRecord:
    id: UUID
    company_id: UUID
    artifact_id: UUID
    transformation_run_id: UUID
    bank_id: str | None
    branch_id: str | None
    account_number: str
    account_type: str | None
    start_date: date | None
    end_date: date | None
    opening_balance: Decimal | None
    closing_balance: Decimal | None
    currency_code: str | None
    sign_policy: str
    created_at: datetime
    receipt_id: UUID | None


@dataclass(frozen=True, slots=True)
class SqlBankTransactionRecord:
    id: UUID
    bank_statement_id: UUID
    transaction_date: date | None
    posted_date: date | None
    amount: Decimal
    direction: str
    description: str | None
    document_number: str | None
    identity_kind: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SqlCatalogRecord:
    id: UUID
    version_no: int
    valid_from: date
    valid_to: date | None
    content: dict[str, object]


@dataclass(frozen=True, slots=True)
class SqlLockRecord:
    lock: AccountLock
    created_at: datetime


class SqlAlchemyOperationalQueryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._journeys = SqlAlchemyJourneyRepository(session)

    def get_company(self, tenant_id: UUID, company_id: UUID) -> SqlCompanyRecord | None:
        row = self._session.scalar(select(CompanyModel).where(
            CompanyModel.tenant_id == tenant_id,
            CompanyModel.id == company_id,
        ))
        if row is None:
            return None
        return SqlCompanyRecord(
            row.id, row.legal_name, row.trade_name, row.tax_identifier,
            row.status, row.timezone, row.currency_code,
        )

    def list_documents(
        self, tenant_id: UUID, company_id: UUID, *, offset: int, limit: int,
        search: str | None, status: str | None, source: str | None,
        received_from: date | None, received_to: date | None,
    ) -> tuple[tuple[SqlDocumentRecord, ...], int]:
        filters = [
            ArtifactReceiptModel.tenant_id == tenant_id,
            ArtifactReceiptModel.company_id == company_id,
        ]
        if search:
            filters.append(ArtifactReceiptModel.original_filename.ilike(f'%{search}%'))
        if status:
            filters.append(or_(
                ImportItemModel.status == status,
                ArtifactReceiptModel.result == status,
                exists(select(TransformationRunModel.id).where(
                    TransformationRunModel.tenant_id == ArtifactReceiptModel.tenant_id,
                    TransformationRunModel.company_id == ArtifactReceiptModel.company_id,
                    TransformationRunModel.artifact_id == ArtifactReceiptModel.artifact_id,
                    TransformationRunModel.status == status,
                )),
            ))
        if source:
            filters.append(ImportBatchModel.source == source)
        if received_from:
            filters.append(ArtifactReceiptModel.received_at >= datetime.combine(received_from, time.min, UTC))
        if received_to:
            filters.append(ArtifactReceiptModel.received_at < datetime.combine(received_to + timedelta(days=1), time.min, UTC))
        joined = (
            select(
                ArtifactReceiptModel, EvidenceArtifactModel, ImportBatchModel,
                ImportItemModel.status, ImportItemModel.error_code,
            )
            .join(EvidenceArtifactModel, and_(
                EvidenceArtifactModel.tenant_id == ArtifactReceiptModel.tenant_id,
                EvidenceArtifactModel.id == ArtifactReceiptModel.artifact_id,
            ))
            .join(ImportBatchModel, and_(
                ImportBatchModel.tenant_id == ArtifactReceiptModel.tenant_id,
                ImportBatchModel.company_id == ArtifactReceiptModel.company_id,
                ImportBatchModel.id == ArtifactReceiptModel.batch_id,
            ))
            .outerjoin(ImportItemModel, and_(
                ImportItemModel.tenant_id == ArtifactReceiptModel.tenant_id,
                ImportItemModel.company_id == ArtifactReceiptModel.company_id,
                ImportItemModel.receipt_id == ArtifactReceiptModel.id,
            ))
            .where(*filters)
        )
        total = int(self._session.scalar(
            select(func.count()).select_from(joined.subquery())
        ) or 0)
        rows = self._session.execute(
            joined.order_by(ArtifactReceiptModel.received_at.desc())
            .offset(offset).limit(limit)
        ).all()
        return tuple(self._document_record(*row) for row in rows), total

    def get_document(
        self, tenant_id: UUID, company_id: UUID, document_id: UUID,
    ) -> SqlDocumentRecord | None:
        row = self._session.execute(
            self._document_query(tenant_id, company_id, document_id).limit(1)
        ).first()
        return None if row is None else self._document_record(*row)

    def _document_query(self, tenant_id: UUID, company_id: UUID, document_id: UUID):
        statement = (
            select(
                ArtifactReceiptModel, EvidenceArtifactModel, ImportBatchModel,
                ImportItemModel.status, ImportItemModel.error_code,
            )
            .join(EvidenceArtifactModel, and_(
                EvidenceArtifactModel.tenant_id == ArtifactReceiptModel.tenant_id,
                EvidenceArtifactModel.id == ArtifactReceiptModel.artifact_id,
            ))
            .join(ImportBatchModel, and_(
                ImportBatchModel.tenant_id == ArtifactReceiptModel.tenant_id,
                ImportBatchModel.company_id == ArtifactReceiptModel.company_id,
                ImportBatchModel.id == ArtifactReceiptModel.batch_id,
            ))
            .outerjoin(ImportItemModel, and_(
                ImportItemModel.tenant_id == ArtifactReceiptModel.tenant_id,
                ImportItemModel.company_id == ArtifactReceiptModel.company_id,
                ImportItemModel.receipt_id == ArtifactReceiptModel.id,
            ))
            .where(
                ArtifactReceiptModel.tenant_id == tenant_id,
                ArtifactReceiptModel.company_id == company_id,
                ArtifactReceiptModel.id == document_id,
            )
        )
        return statement

    def list_document_issues(
        self, tenant_id: UUID, company_id: UUID, artifact_id: UUID,
    ) -> tuple[ValidationIssue, ...]:
        rows = self._session.scalars(
            select(ValidationIssueModel)
            .join(TransformationRunModel, and_(
                TransformationRunModel.tenant_id == ValidationIssueModel.tenant_id,
                TransformationRunModel.company_id == ValidationIssueModel.company_id,
                TransformationRunModel.id == ValidationIssueModel.transformation_run_id,
            ))
            .where(
                ValidationIssueModel.tenant_id == tenant_id,
                ValidationIssueModel.company_id == company_id,
                TransformationRunModel.artifact_id == artifact_id,
            )
            .order_by(ValidationIssueModel.created_at.desc())
        )
        return tuple(_issue(row) for row in rows)

    def linked_fiscal_document_id(
        self, tenant_id: UUID, company_id: UUID, artifact_id: UUID,
    ) -> UUID | None:
        return self._session.scalar(select(FiscalDocumentModel.id).where(
            FiscalDocumentModel.tenant_id == tenant_id,
            FiscalDocumentModel.company_id == company_id,
            FiscalDocumentModel.artifact_id == artifact_id,
        ).limit(1))

    def linked_bank_statement_id(
        self, tenant_id: UUID, company_id: UUID, artifact_id: UUID,
    ) -> UUID | None:
        return self._session.scalar(select(BankStatementModel.id).where(
            BankStatementModel.tenant_id == tenant_id,
            BankStatementModel.company_id == company_id,
            BankStatementModel.artifact_id == artifact_id,
        ).limit(1))

    def _document_record(
        self, receipt: ArtifactReceiptModel, artifact: EvidenceArtifactModel,
        batch: ImportBatchModel, item_status: str | None, error_code: str | None,
    ) -> SqlDocumentRecord:
        run = self._session.scalar(
            select(TransformationRunModel).where(
                TransformationRunModel.tenant_id == receipt.tenant_id,
                TransformationRunModel.company_id == receipt.company_id,
                TransformationRunModel.artifact_id == receipt.artifact_id,
            ).order_by(TransformationRunModel.started_at.desc()).limit(1)
        )
        return SqlDocumentRecord(
            receipt.id, receipt.company_id, receipt.batch_id, receipt.artifact_id,
            receipt.original_filename, artifact.media_type, artifact.size_bytes,
            batch.source, receipt.channel, receipt.result,
            run.status if run is not None else (item_status or receipt.result),
            error_code, receipt.received_at,
        )

    def document_counts(self, tenant_id: UUID, company_id: UUID) -> tuple[int, int, int]:
        received = int(self._session.scalar(select(func.count()).select_from(ArtifactReceiptModel).where(
            ArtifactReceiptModel.tenant_id == tenant_id,
            ArtifactReceiptModel.company_id == company_id,
        )) or 0)
        processed = int(self._session.scalar(select(func.count(func.distinct(TransformationRunModel.artifact_id))).where(
            TransformationRunModel.tenant_id == tenant_id,
            TransformationRunModel.company_id == company_id,
            TransformationRunModel.status == 'COMPLETED',
        )) or 0)
        attention = int(self._session.scalar(
            select(func.count(func.distinct(TransformationRunModel.artifact_id)))
            .join(ValidationIssueModel, and_(
                ValidationIssueModel.tenant_id == TransformationRunModel.tenant_id,
                ValidationIssueModel.company_id == TransformationRunModel.company_id,
                ValidationIssueModel.transformation_run_id == TransformationRunModel.id,
            )).where(
            TransformationRunModel.tenant_id == tenant_id,
            TransformationRunModel.company_id == company_id,
            ValidationIssueModel.resolution_status != 'RESOLVED',
        )) or 0)
        return received, processed, attention

    def list_fiscal_documents(
        self, tenant_id: UUID, company_id: UUID, *, offset: int, limit: int,
        search: str | None, status: str | None, issued_from: date | None,
        issued_to: date | None,
    ) -> tuple[tuple[SqlFiscalRecord, ...], int]:
        filters = [FiscalDocumentModel.tenant_id == tenant_id, FiscalDocumentModel.company_id == company_id]
        if search:
            filters.append(or_(
                FiscalDocumentModel.access_key.ilike(f'%{search}%'),
                FiscalDocumentModel.document_number.ilike(f'%{search}%'),
                FiscalDocumentModel.issuer_name.ilike(f'%{search}%'),
            ))
        if status:
            filters.append(FiscalDocumentModel.observed_status == status)
        if issued_from:
            filters.append(FiscalDocumentModel.issued_at >= datetime.combine(issued_from, time.min, UTC))
        if issued_to:
            filters.append(FiscalDocumentModel.issued_at < datetime.combine(issued_to + timedelta(days=1), time.min, UTC))
        total = int(self._session.scalar(select(func.count()).select_from(FiscalDocumentModel).where(*filters)) or 0)
        rows = self._session.scalars(select(FiscalDocumentModel).where(*filters).order_by(
            FiscalDocumentModel.issued_at.desc(), FiscalDocumentModel.created_at.desc(),
        ).offset(offset).limit(limit))
        return tuple(self._fiscal_record(row) for row in rows), total

    def get_fiscal_document(
        self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID,
    ) -> SqlFiscalRecord | None:
        row = self._session.scalar(select(FiscalDocumentModel).where(
            FiscalDocumentModel.tenant_id == tenant_id,
            FiscalDocumentModel.company_id == company_id,
            FiscalDocumentModel.id == fiscal_document_id,
        ))
        return None if row is None else self._fiscal_record(row)

    def list_fiscal_items(
        self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID,
        *, limit: int,
    ) -> tuple[tuple[SqlFiscalItemRecord, ...], int]:
        filters = [
            FiscalDocumentItemModel.tenant_id == tenant_id,
            FiscalDocumentItemModel.company_id == company_id,
            FiscalDocumentItemModel.fiscal_document_id == fiscal_document_id,
        ]
        total = int(self._session.scalar(select(func.count()).select_from(FiscalDocumentItemModel).where(*filters)) or 0)
        rows = self._session.scalars(select(FiscalDocumentItemModel).where(*filters).order_by(
            FiscalDocumentItemModel.sequence,
        ).limit(limit))
        return tuple(SqlFiscalItemRecord(
            row.id, row.sequence, row.product_code, row.description, row.ncm,
            row.cfop, row.commercial_unit, row.quantity, row.unit_value,
            row.gross_total, row.discount_total, row.other_total,
            row.included_in_total,
        ) for row in rows), total

    def fiscal_tax_totals(
        self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID,
    ) -> tuple[tuple[str, Decimal], ...]:
        rows = self._session.execute(
            select(TaxDetailModel.tax_type, func.sum(TaxDetailModel.amount))
            .join(FiscalDocumentItemModel, and_(
                FiscalDocumentItemModel.tenant_id == TaxDetailModel.tenant_id,
                FiscalDocumentItemModel.company_id == TaxDetailModel.company_id,
                FiscalDocumentItemModel.id == TaxDetailModel.fiscal_document_item_id,
            )).where(
                TaxDetailModel.tenant_id == tenant_id,
                TaxDetailModel.company_id == company_id,
                FiscalDocumentItemModel.fiscal_document_id == fiscal_document_id,
            ).group_by(TaxDetailModel.tax_type).order_by(TaxDetailModel.tax_type)
        )
        return tuple((str(tax_type), amount or Decimal('0')) for tax_type, amount in rows)

    def list_bank_statements(
        self, tenant_id: UUID, company_id: UUID, *, offset: int, limit: int,
    ) -> tuple[tuple[SqlBankStatementRecord, ...], int]:
        filters = [BankStatementModel.tenant_id == tenant_id, BankStatementModel.company_id == company_id]
        total = int(self._session.scalar(select(func.count()).select_from(BankStatementModel).where(*filters)) or 0)
        rows = self._session.execute(
            select(BankStatementModel, BankAccountModel).join(BankAccountModel, and_(
                BankAccountModel.tenant_id == BankStatementModel.tenant_id,
                BankAccountModel.company_id == BankStatementModel.company_id,
                BankAccountModel.id == BankStatementModel.bank_account_id,
            )).where(*filters).order_by(BankStatementModel.created_at.desc()).offset(offset).limit(limit)
        )
        return tuple(self._bank_statement_record(*row) for row in rows), total

    def get_bank_statement(
        self, tenant_id: UUID, company_id: UUID, statement_id: UUID,
    ) -> SqlBankStatementRecord | None:
        row = self._session.execute(
            select(BankStatementModel, BankAccountModel).join(BankAccountModel, and_(
                BankAccountModel.tenant_id == BankStatementModel.tenant_id,
                BankAccountModel.company_id == BankStatementModel.company_id,
                BankAccountModel.id == BankStatementModel.bank_account_id,
            )).where(
                BankStatementModel.tenant_id == tenant_id,
                BankStatementModel.company_id == company_id,
                BankStatementModel.id == statement_id,
            ).limit(1)
        ).first()
        return None if row is None else self._bank_statement_record(*row)

    def list_bank_transactions(
        self, tenant_id: UUID, company_id: UUID, statement_id: UUID, *,
        offset: int, limit: int, search: str | None, direction: str | None,
        posted_from: date | None, posted_to: date | None,
    ) -> tuple[tuple[SqlBankTransactionRecord, ...], int]:
        filters = [
            BankTransactionModel.tenant_id == tenant_id,
            BankTransactionModel.company_id == company_id,
            BankTransactionModel.bank_statement_id == statement_id,
        ]
        if search:
            filters.append(BankTransactionModel.description.ilike(f'%{search}%'))
        if direction:
            filters.append(BankTransactionModel.direction == direction)
        if posted_from:
            filters.append(BankTransactionModel.posted_date >= posted_from)
        if posted_to:
            filters.append(BankTransactionModel.posted_date <= posted_to)
        total = int(self._session.scalar(select(func.count()).select_from(BankTransactionModel).where(*filters)) or 0)
        rows = self._session.scalars(select(BankTransactionModel).where(*filters).order_by(
            BankTransactionModel.posted_date.desc(), BankTransactionModel.created_at.desc(),
        ).offset(offset).limit(limit))
        return tuple(SqlBankTransactionRecord(
            row.id, row.bank_statement_id, row.transaction_date, row.posted_date,
            row.amount, row.direction, row.description, row.document_number,
            row.identity_kind, row.created_at,
        ) for row in rows), total

    def _receipt_id(self, tenant_id: UUID, company_id: UUID, artifact_id: UUID) -> UUID | None:
        return self._session.scalar(select(ArtifactReceiptModel.id).where(
            ArtifactReceiptModel.tenant_id == tenant_id,
            ArtifactReceiptModel.company_id == company_id,
            ArtifactReceiptModel.artifact_id == artifact_id,
        ).order_by(ArtifactReceiptModel.received_at).limit(1))

    def _fiscal_record(self, row: FiscalDocumentModel) -> SqlFiscalRecord:
        return SqlFiscalRecord(
            row.id, row.company_id, row.artifact_id, row.access_key, row.model,
            row.schema_version, row.series, row.document_number,
            row.operation_nature, row.issuer_tax_id, row.issuer_name,
            row.recipient_tax_id, row.recipient_name, row.issued_at,
            row.movement_at, row.products_total, row.freight_total,
            row.insurance_total, row.discount_total, row.other_total,
            row.tax_total, row.invoice_total, row.observed_status,
            row.protocol_status_code, row.protocol_status_reason, row.created_at,
            self._receipt_id(row.tenant_id, row.company_id, row.artifact_id),
        )

    def _bank_statement_record(
        self, row: BankStatementModel, account: BankAccountModel,
    ) -> SqlBankStatementRecord:
        return SqlBankStatementRecord(
            row.id, row.company_id, row.artifact_id, row.transformation_run_id,
            account.bank_id,
            account.branch_id, account.account_number, account.account_type,
            row.start_date, row.end_date, row.opening_balance,
            row.closing_balance, row.currency_code, row.sign_policy,
            row.created_at,
            self._receipt_id(row.tenant_id, row.company_id, row.artifact_id),
        )

    def get_batch(
        self, tenant_id: UUID, company_id: UUID, batch_id: UUID,
    ) -> ImportBatch | None:
        row = self._session.scalar(select(ImportBatchModel).where(
            ImportBatchModel.tenant_id == tenant_id,
            ImportBatchModel.company_id == company_id,
            ImportBatchModel.id == batch_id,
        ))
        return None if row is None else _batch(row)

    def batch_content_hash(
        self, tenant_id: UUID, company_id: UUID, batch_id: UUID,
    ) -> str | None:
        return self._session.scalar(
            select(EvidenceArtifactModel.content_hash)
            .join(ArtifactReceiptModel, (
                ArtifactReceiptModel.tenant_id == EvidenceArtifactModel.tenant_id
            ) & (
                ArtifactReceiptModel.artifact_id == EvidenceArtifactModel.id
            ))
            .where(
                ArtifactReceiptModel.tenant_id == tenant_id,
                ArtifactReceiptModel.company_id == company_id,
                ArtifactReceiptModel.batch_id == batch_id,
            ).order_by(ArtifactReceiptModel.received_at).limit(1)
        )

    def list_journeys(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[Journey, ...]:
        ids = tuple(self._session.scalars(
            select(JourneyCheckpointModel.journey_id)
            .where(
                JourneyCheckpointModel.tenant_id == tenant_id,
                JourneyCheckpointModel.company_id == company_id,
            )
            .group_by(JourneyCheckpointModel.journey_id)
            .order_by(func.max(JourneyCheckpointModel.created_at).desc())
            .limit(limit)
        ))
        return tuple(
            journey for journey_id in ids
            if (journey := self._journeys.get(
                tenant_id, company_id, journey_id,
            )) is not None
        )

    def list_proposal_journeys(
        self, tenant_id: UUID, company_id: UUID, *, offset: int, limit: int,
        status: str | None,
    ) -> tuple[tuple[Journey, ...], int]:
        proposal_statuses = (
            'PENDING_APPROVAL', 'APPROVED', 'REJECTED',
            'BLOCKED_FOR_HOMOLOGATION', 'SUPERSEDED',
        )
        latest = select(
            JourneyCheckpointModel.journey_id,
            func.max(JourneyCheckpointModel.version).label('latest_version'),
        ).where(
            JourneyCheckpointModel.tenant_id == tenant_id,
            JourneyCheckpointModel.company_id == company_id,
        ).group_by(JourneyCheckpointModel.journey_id).subquery()
        filters = [
            JourneyCheckpointModel.tenant_id == tenant_id,
            JourneyCheckpointModel.company_id == company_id,
            JourneyCheckpointModel.status.in_(proposal_statuses),
        ]
        if status:
            filters.append(JourneyCheckpointModel.status == status)
        current = select(JourneyCheckpointModel).join(
            latest, and_(
                latest.c.journey_id == JourneyCheckpointModel.journey_id,
                latest.c.latest_version == JourneyCheckpointModel.version,
            ),
        ).where(*filters)
        total = int(self._session.scalar(
            select(func.count()).select_from(current.subquery()),
        ) or 0)
        ids = tuple(self._session.scalars(
            current.with_only_columns(JourneyCheckpointModel.journey_id)
            .order_by(JourneyCheckpointModel.created_at.desc())
            .offset(offset).limit(limit)
        ))
        return tuple(
            journey for journey_id in ids
            if (journey := self._journeys.get(tenant_id, company_id, journey_id)) is not None
        ), total

    def published_catalog(
        self, tenant_id: UUID, company_id: UUID, *, at: date,
    ) -> SqlCatalogRecord | None:
        model = self._session.scalar(select(ProductionCatalogVersionModel).where(
            ProductionCatalogVersionModel.tenant_id == tenant_id,
            ProductionCatalogVersionModel.company_id == company_id,
            ProductionCatalogVersionModel.status == 'PUBLISHED',
            ProductionCatalogVersionModel.valid_from <= at,
            or_(
                ProductionCatalogVersionModel.valid_to.is_(None),
                ProductionCatalogVersionModel.valid_to >= at,
            ),
        ).order_by(ProductionCatalogVersionModel.version_no.desc()).limit(1))
        if model is None:
            return None
        if snapshot_hash(model.content) != model.content_hash:
            raise ValueError('catalog integrity invalid')
        return SqlCatalogRecord(
            model.id, model.version_no, model.valid_from, model.valid_to, model.content,
        )

    def rule_name(
        self, tenant_id: UUID, company_id: UUID, rule_version_id: UUID,
    ) -> str | None:
        versions = self._session.scalars(select(ProductionCatalogVersionModel).where(
            ProductionCatalogVersionModel.tenant_id == tenant_id,
            ProductionCatalogVersionModel.company_id == company_id,
            ProductionCatalogVersionModel.status == 'PUBLISHED',
        ).order_by(ProductionCatalogVersionModel.version_no.desc()))
        target = str(rule_version_id)
        for version in versions:
            if snapshot_hash(version.content) != version.content_hash:
                raise ValueError('catalog integrity invalid')
            for rule in version.content.get('rules', []):
                if isinstance(rule, dict) and rule.get('id') == target:
                    return str(rule.get('name') or '') or None
        return None

    def list_active_lock_records(
        self, tenant_id: UUID, company_id: UUID,
    ) -> tuple[SqlLockRecord, ...]:
        rows = self._session.scalars(select(AccountLockModel).where(
            AccountLockModel.tenant_id == tenant_id,
            AccountLockModel.company_id == company_id,
            AccountLockModel.status == LockStatus.ACTIVE.value,
        ).order_by(AccountLockModel.created_at.desc()))
        return tuple(SqlLockRecord(AccountLock(
            row.id, row.tenant_id, row.company_id, LockScope(row.scope),
            tuple(EffectOperation(value) for value in row.operations), row.reason,
            LockStatus(row.status), row.account_id, row.group_id, row.module,
            row.competence, row.exercise, row.released_by, row.released_at,
            row.release_reason,
        ), row.created_at) for row in rows)

    def list_audit_events_by_correlation(
        self, tenant_id: UUID, company_id: UUID, correlation_id: UUID, *, limit: int,
    ) -> tuple[AuditEvent, ...]:
        rows = self._session.scalars(select(AuditEventModel).where(
            AuditEventModel.tenant_id == tenant_id,
            AuditEventModel.company_id == company_id,
            AuditEventModel.correlation_id == correlation_id,
        ).order_by(AuditEventModel.occurred_at.desc()).limit(limit))
        return tuple(_audit(row) for row in rows)

    def find_trace_correlation_ids(
        self, tenant_id: UUID, company_id: UUID,
        references: tuple[tuple[str, UUID], ...], *, limit: int,
    ) -> tuple[UUID, ...]:
        if not references:
            return ()
        subjects = or_(*(
            and_(AuditEventModel.subject_type == subject_type,
                 AuditEventModel.subject_id == subject_id)
            for subject_type, subject_id in references
        ))
        rows = self._session.scalars(select(AuditEventModel.correlation_id).where(
            AuditEventModel.tenant_id == tenant_id,
            AuditEventModel.company_id == company_id,
            subjects,
        ).distinct().order_by(AuditEventModel.correlation_id).limit(limit))
        return tuple(rows)

    def list_trace_audit_events(
        self, tenant_id: UUID, company_id: UUID,
        correlation_ids: tuple[UUID, ...], *, limit: int,
    ) -> tuple[AuditEvent, ...]:
        if not correlation_ids:
            return ()
        rows = self._session.scalars(select(AuditEventModel).where(
            AuditEventModel.tenant_id == tenant_id,
            AuditEventModel.company_id == company_id,
            AuditEventModel.correlation_id.in_(correlation_ids),
        ).order_by(
            AuditEventModel.occurred_at.desc(), AuditEventModel.id.desc(),
        ).limit(limit))
        return tuple(_audit(row) for row in rows)

    def actor_display_names(
        self, tenant_id: UUID, actor_ids: tuple[UUID, ...],
    ) -> dict[UUID, str]:
        if not actor_ids:
            return {}
        rows = self._session.execute(select(UserModel.id, UserModel.display_name).join(
            TenantMembershipModel,
            TenantMembershipModel.user_id == UserModel.id,
        ).where(
            TenantMembershipModel.tenant_id == tenant_id,
            UserModel.id.in_(actor_ids),
        ).distinct())
        return {user_id: display_name for user_id, display_name in rows}

    def get_journey(
        self, tenant_id: UUID, company_id: UUID, journey_id: UUID,
    ) -> Journey | None:
        return self._journeys.get(tenant_id, company_id, journey_id)

    def get_journey_by_fiscal_document(
        self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID,
    ) -> Journey | None:
        journey_id = self._session.scalar(select(JourneyCheckpointModel.journey_id).where(
            JourneyCheckpointModel.tenant_id == tenant_id,
            JourneyCheckpointModel.company_id == company_id,
            JourneyCheckpointModel.fiscal_document_id == fiscal_document_id,
        ).order_by(
            JourneyCheckpointModel.version.desc(),
            JourneyCheckpointModel.created_at.desc(),
        ).limit(1))
        return (
            self._journeys.get(tenant_id, company_id, journey_id)
            if journey_id is not None else None
        )

    def list_issues(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[ValidationIssue, ...]:
        rows = self._session.scalars(select(ValidationIssueModel).where(
            ValidationIssueModel.tenant_id == tenant_id,
            ValidationIssueModel.company_id == company_id,
        ).order_by(ValidationIssueModel.created_at.desc()).limit(limit))
        return tuple(_issue(row) for row in rows)

    def list_audit_events(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[AuditEvent, ...]:
        rows = self._session.scalars(select(AuditEventModel).where(
            AuditEventModel.tenant_id == tenant_id,
            AuditEventModel.company_id == company_id,
        ).order_by(AuditEventModel.occurred_at.desc()).limit(limit))
        return tuple(_audit(row) for row in rows)


def _batch(row: ImportBatchModel) -> ImportBatch:
    return ImportBatch(
        row.id, row.tenant_id, row.company_id, row.source,
        row.idempotency_key, row.status, row.total_items,
        row.received_items, row.duplicate_items, row.failed_items,
        row.started_at, row.completed_at, row.revision,
    )


def _issue(row: ValidationIssueModel) -> ValidationIssue:
    return ValidationIssue(
        row.id, row.tenant_id, row.company_id, row.transformation_run_id,
        row.code, row.severity, row.field_path, row.rule_reference,
        row.message, row.resolution_status, row.created_at,
    )


def _audit(row: AuditEventModel) -> AuditEvent:
    return AuditEvent(
        row.id, row.tenant_id, row.company_id, row.actor_id,
        AuditOrigin(row.origin), row.module, row.action, row.subject_type,
        row.subject_id, row.subject_version, row.before_state, row.after_state,
        row.reason, row.correlation_id, row.causation_id, row.occurred_at,
        row.integrity_hash,
    )
