'''Porta de leitura operacional, sempre escopada por tenant e empresa.'''

from datetime import date, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from serdial21.modules.audit.domain.entities import AuditEvent
from serdial21.modules.intake_documents.domain.entities import ImportBatch, ValidationIssue
from serdial21.modules.locks.domain.entities import AccountLock
from serdial21.modules.workflow.application.journey import Journey
from serdial21.modules.operations.domain.entities import DomainEvent, InboxReceipt, OutboxMessage


class CompanyRecord(Protocol):
    id: UUID
    legal_name: str
    trade_name: str | None
    tax_identifier: str
    status: str
    timezone: str
    currency_code: str


class DocumentRecord(Protocol):
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


class FiscalRecord(Protocol):
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


class FiscalItemRecord(Protocol):
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


class BankStatementRecord(Protocol):
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


class BankTransactionRecord(Protocol):
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


class CatalogRecord(Protocol):
    id: UUID
    version_no: int
    valid_from: date
    valid_to: date | None
    content: dict[str, object]


class LockRecord(Protocol):
    lock: AccountLock
    created_at: datetime


class OperationRepository(Protocol):
    '''Persiste efeito crítico, inbox e outbox na mesma unidade de trabalho.'''

    def find_inbox_receipt(
        self, tenant_id: UUID, company_id: UUID, consumer: str,
        idempotency_key: str,
    ) -> InboxReceipt | None: ...

    def commit_effect_with_messages(
        self, *, result_id: UUID, event: DomainEvent, outbox: OutboxMessage,
        receipt: InboxReceipt,
    ) -> None: ...


class OperationalQueryRepository(Protocol):
    def get_company(self, tenant_id: UUID, company_id: UUID) -> CompanyRecord | None: ...

    def list_documents(
        self, tenant_id: UUID, company_id: UUID, *, offset: int, limit: int,
        search: str | None, status: str | None, source: str | None,
        received_from: date | None, received_to: date | None,
    ) -> tuple[tuple[DocumentRecord, ...], int]: ...

    def get_document(
        self, tenant_id: UUID, company_id: UUID, document_id: UUID,
    ) -> DocumentRecord | None: ...

    def list_document_issues(
        self, tenant_id: UUID, company_id: UUID, artifact_id: UUID,
    ) -> tuple[ValidationIssue, ...]: ...

    def linked_fiscal_document_id(
        self, tenant_id: UUID, company_id: UUID, artifact_id: UUID,
    ) -> UUID | None: ...

    def linked_bank_statement_id(
        self, tenant_id: UUID, company_id: UUID, artifact_id: UUID,
    ) -> UUID | None: ...

    def document_counts(self, tenant_id: UUID, company_id: UUID) -> tuple[int, int, int]: ...

    def list_fiscal_documents(
        self, tenant_id: UUID, company_id: UUID, *, offset: int, limit: int,
        search: str | None, status: str | None, issued_from: date | None,
        issued_to: date | None,
    ) -> tuple[tuple[FiscalRecord, ...], int]: ...

    def get_fiscal_document(
        self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID,
    ) -> FiscalRecord | None: ...

    def list_fiscal_items(
        self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID,
        *, limit: int,
    ) -> tuple[tuple[FiscalItemRecord, ...], int]: ...

    def fiscal_tax_totals(
        self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID,
    ) -> tuple[tuple[str, Decimal], ...]: ...

    def list_bank_statements(
        self, tenant_id: UUID, company_id: UUID, *, offset: int, limit: int,
    ) -> tuple[tuple[BankStatementRecord, ...], int]: ...

    def get_bank_statement(
        self, tenant_id: UUID, company_id: UUID, statement_id: UUID,
    ) -> BankStatementRecord | None: ...

    def list_bank_transactions(
        self, tenant_id: UUID, company_id: UUID, statement_id: UUID, *,
        offset: int, limit: int, search: str | None, direction: str | None,
        posted_from: date | None, posted_to: date | None,
    ) -> tuple[tuple[BankTransactionRecord, ...], int]: ...

    def get_batch(
        self, tenant_id: UUID, company_id: UUID, batch_id: UUID,
    ) -> ImportBatch | None: ...

    def batch_content_hash(
        self, tenant_id: UUID, company_id: UUID, batch_id: UUID,
    ) -> str | None: ...

    def list_journeys(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[Journey, ...]: ...

    def list_proposal_journeys(
        self, tenant_id: UUID, company_id: UUID, *, offset: int, limit: int,
        status: str | None,
    ) -> tuple[tuple[Journey, ...], int]: ...

    def published_catalog(
        self, tenant_id: UUID, company_id: UUID, *, at: date,
    ) -> CatalogRecord | None: ...

    def rule_name(
        self, tenant_id: UUID, company_id: UUID, rule_version_id: UUID,
    ) -> str | None: ...

    def list_active_lock_records(
        self, tenant_id: UUID, company_id: UUID,
    ) -> tuple[LockRecord, ...]: ...

    def list_audit_events_by_correlation(
        self, tenant_id: UUID, company_id: UUID, correlation_id: UUID, *, limit: int,
    ) -> tuple[AuditEvent, ...]: ...

    def find_trace_correlation_ids(
        self, tenant_id: UUID, company_id: UUID,
        references: tuple[tuple[str, UUID], ...], *, limit: int,
    ) -> tuple[UUID, ...]: ...

    def list_trace_audit_events(
        self, tenant_id: UUID, company_id: UUID,
        correlation_ids: tuple[UUID, ...], *, limit: int,
    ) -> tuple[AuditEvent, ...]: ...

    def actor_display_names(
        self, tenant_id: UUID, actor_ids: tuple[UUID, ...],
    ) -> dict[UUID, str]: ...

    def get_journey(
        self, tenant_id: UUID, company_id: UUID, journey_id: UUID,
    ) -> Journey | None: ...

    def get_journey_by_fiscal_document(
        self, tenant_id: UUID, company_id: UUID, fiscal_document_id: UUID,
    ) -> Journey | None: ...

    def list_issues(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[ValidationIssue, ...]: ...

    def list_audit_events(
        self, tenant_id: UUID, company_id: UUID, *, limit: int,
    ) -> tuple[AuditEvent, ...]: ...
