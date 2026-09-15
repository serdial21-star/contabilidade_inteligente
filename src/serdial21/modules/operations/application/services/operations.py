'''Orquestra contratos operacionais sem mover regras dos domínios de origem.'''

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
from uuid import UUID

from serdial21.modules.access_control.application.services.authorization import (
    AuthorizationRequest, AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.banking.application.services.ofx_importer import (
    OfxImportRequest, OfxImportResult, OfxImportService,
)
from serdial21.modules.intake_documents.application.services.intake import (
    DocumentIntakeService, IntakeContext, StartBatchRequest,
)
from serdial21.modules.intake_documents.domain.entities import ImportBatch
from serdial21.modules.locks.domain.entities import (
    AccountLock, AccountLockedError, EffectChannel, EffectContext,
    EffectOperation, validate_effect,
)
from serdial21.modules.operations.application.ports.repository import OperationalQueryRepository
from serdial21.modules.operations.application.services.traceability import (
    DecisionLine, DecisionLineRoot, DecisionLineService,
)
from serdial21.modules.workflow.application.journey import Journey, JourneyCommand
from serdial21.modules.workflow.application.services.nfe_to_dominio import NFeToDominioService


class OperationalConflictError(RuntimeError):
    '''Conflito estável de idempotência ou concorrência.'''


class OperationalUnavailableError(LookupError):
    '''Ausente e fora do escopo são indistinguíveis.'''


@dataclass(frozen=True, slots=True)
class NFeImportCommand:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID
    idempotency_key: str
    accounting_date: date
    period_start: date
    period_end: date
    approval_expires_at: datetime
    content: bytes
    filename: str
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class OfxImportCommand:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID
    idempotency_key: str
    content: bytes
    filename: str
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class ProcessingView:
    id: UUID
    kind: str
    source: str
    status: str
    total_items: int
    received_items: int
    duplicate_items: int
    failed_items: int
    started_at: datetime | None
    completed_at: datetime | None
    revision: int


@dataclass(frozen=True, slots=True)
class ReviewSummary:
    journey_id: UUID
    version: int
    status: str
    revision_id: UUID
    revision_hash: str
    accounting_date: date
    request_id: UUID | None
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class ReviewLineView:
    account_version_id: UUID
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal


@dataclass(frozen=True, slots=True)
class ReviewDetail:
    summary: ReviewSummary
    proposer_id: UUID
    validation_status: str | None
    lines: tuple[ReviewLineView, ...]
    source_count: int


@dataclass(frozen=True, slots=True)
class AccountingProposalSummary:
    journey_id: UUID
    company_id: UUID
    version: int
    status: str
    proposal_id: UUID
    revision_id: UUID
    revision_hash: str
    accounting_date: date
    source_type: str
    source_id: UUID
    source_document_receipt_id: UUID | None
    rule_version_id: UUID
    rule_name: str | None
    total_debit: Decimal
    total_credit: Decimal
    balanced: bool
    validation_status: str | None
    proposer_id: UUID
    approval_role: str
    responsible_role: str
    expires_at: datetime | None
    decision_actor_id: UUID | None
    decided_at: datetime | None


@dataclass(frozen=True, slots=True)
class AccountingProposalPage:
    items: tuple[AccountingProposalSummary, ...]
    total: int
    offset: int
    limit: int


@dataclass(frozen=True, slots=True)
class RuleConditionView:
    field: str
    operator: str
    value: str


@dataclass(frozen=True, slots=True)
class AccountingRuleView:
    id: UUID
    name: str | None
    scope: str
    priority: int
    status: str
    automation_level: str
    conditions: tuple[RuleConditionView, ...]
    debit_account_version_id: UUID
    debit_account_code: str
    debit_account_name: str
    credit_account_version_id: UUID
    credit_account_code: str
    credit_account_name: str


@dataclass(frozen=True, slots=True)
class AccountingSourceEvidence:
    source_type: str
    source_id: UUID
    document_receipt_id: UUID | None
    document_number: str | None
    issuer_name: str | None
    issued_at: datetime | None
    amount: Decimal | None


@dataclass(frozen=True, slots=True)
class AccountingLockView:
    id: UUID
    scope: str
    operations: tuple[str, ...]
    reason: str
    target: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AccountingProposalDetail:
    summary: AccountingProposalSummary
    rule: AccountingRuleView
    lines: tuple[ReviewLineView, ...]
    sources: tuple[AccountingSourceEvidence, ...]
    active_locks: tuple[AccountingLockView, ...]


@dataclass(frozen=True, slots=True)
class AccountingAccountView:
    id: UUID
    code: str
    name: str
    nature: str
    normal_balance: str
    is_synthetic: bool
    is_postable: bool
    status: str


@dataclass(frozen=True, slots=True)
class AccountingMappingView:
    id: UUID
    key: str
    priority: int
    external_code: str | None
    history_contains: str | None
    dimension_code: str | None
    canonical_entity: str | None
    target_account_version_id: UUID
    target_account_code: str
    target_account_name: str


@dataclass(frozen=True, slots=True)
class AccountingCatalogView:
    version_id: UUID
    version_no: int
    valid_from: date
    valid_to: date | None
    decimal_places: int
    amount_field: str
    rules: tuple[AccountingRuleView, ...]
    accounts: tuple[AccountingAccountView, ...]
    mappings: tuple[AccountingMappingView, ...]


@dataclass(frozen=True, slots=True)
class ExceptionView:
    id: UUID
    transformation_run_id: UUID
    code: str
    severity: str
    field_path: str | None
    rule_reference: str | None
    resolution_status: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuditView:
    id: UUID
    actor_id: UUID | None
    origin: str
    module: str
    action: str
    subject_type: str
    subject_id: UUID
    subject_version: int | None
    correlation_id: UUID
    occurred_at: datetime
    integrity_valid: bool


@dataclass(frozen=True, slots=True)
class CompanyView:
    id: UUID
    legal_name: str
    trade_name: str | None
    tax_identifier: str
    status: str
    timezone: str
    currency_code: str


@dataclass(frozen=True, slots=True)
class DocumentView:
    id: UUID
    company_id: UUID
    batch_id: UUID
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
class DocumentPage:
    items: tuple[DocumentView, ...]
    total: int
    offset: int
    limit: int


@dataclass(frozen=True, slots=True)
class DocumentDetail:
    document: DocumentView
    issues: tuple[ExceptionView, ...]
    fiscal_document_id: UUID | None
    bank_statement_id: UUID | None


@dataclass(frozen=True, slots=True)
class DocumentSummary:
    received: int
    processed: int
    attention_required: int


@dataclass(frozen=True, slots=True)
class FiscalDocumentView:
    id: UUID
    company_id: UUID
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
    document_receipt_id: UUID | None


@dataclass(frozen=True, slots=True)
class FiscalItemView:
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
class FiscalPage:
    items: tuple[FiscalDocumentView, ...]
    total: int
    offset: int
    limit: int


@dataclass(frozen=True, slots=True)
class FiscalDetail:
    document: FiscalDocumentView
    items: tuple[FiscalItemView, ...]
    item_count: int
    tax_totals: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True, slots=True)
class BankStatementView:
    id: UUID
    company_id: UUID
    bank_id: str | None
    branch_masked: str | None
    account_masked: str
    account_type: str | None
    start_date: date | None
    end_date: date | None
    opening_balance: Decimal | None
    closing_balance: Decimal | None
    currency_code: str | None
    sign_policy: str
    imported_at: datetime
    document_receipt_id: UUID | None


@dataclass(frozen=True, slots=True)
class BankStatementPage:
    items: tuple[BankStatementView, ...]
    total: int
    offset: int
    limit: int


@dataclass(frozen=True, slots=True)
class BankTransactionView:
    id: UUID
    bank_statement_id: UUID
    transaction_date: date | None
    posted_date: date | None
    amount: Decimal
    direction: str
    description: str | None
    document_number: str | None
    identity_kind: str


@dataclass(frozen=True, slots=True)
class BankTransactionPage:
    items: tuple[BankTransactionView, ...]
    total: int
    offset: int
    limit: int


@dataclass(frozen=True, slots=True)
class BankStatementDetail:
    statement: BankStatementView
    transactions: BankTransactionPage


class OperationalService:
    def __init__(
        self, repository: OperationalQueryRepository,
        authorization: AuthorizationService, intake: DocumentIntakeService,
        nfe: NFeToDominioService, ofx: OfxImportService, audit: AuditService,
    ) -> None:
        self._repository = repository
        self._authorization = authorization
        self._intake = intake
        self._nfe = nfe
        self._ofx = ofx
        self._audit = audit
        self._traceability = DecisionLineService(repository, authorization, audit)

    def company(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
    ) -> CompanyView:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        row = self._repository.get_company(tenant_id, company_id)
        if row is None:
            raise OperationalUnavailableError()
        return CompanyView(
            row.id, row.legal_name, row.trade_name, row.tax_identifier,
            row.status, row.timezone, row.currency_code,
        )

    def documents(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *,
        offset: int, limit: int, search: str | None = None,
        status: str | None = None, source: str | None = None,
        received_from: date | None = None, received_to: date | None = None,
    ) -> DocumentPage:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        if received_from is not None and received_to is not None and received_from > received_to:
            raise ValueError('invalid date range')
        rows, total = self._repository.list_documents(
            tenant_id, company_id, offset=offset, limit=limit,
            search=search, status=status, source=source,
            received_from=received_from, received_to=received_to,
        )
        return DocumentPage(
            tuple(_document_view(row) for row in rows), total, offset, limit,
        )

    def document(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, document_id: UUID,
    ) -> DocumentDetail:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        row = self._repository.get_document(tenant_id, company_id, document_id)
        if row is None:
            raise OperationalUnavailableError()
        issues = self._repository.list_document_issues(
            tenant_id, company_id, row.artifact_id,
        )
        return DocumentDetail(_document_view(row), tuple(ExceptionView(
            item.id, item.transformation_run_id, item.code, item.severity,
            item.field_path, item.rule_reference, item.resolution_status,
            item.created_at,
        ) for item in issues), self._repository.linked_fiscal_document_id(
            tenant_id, company_id, row.artifact_id,
        ), self._repository.linked_bank_statement_id(
            tenant_id, company_id, row.artifact_id,
        ))

    def document_summary(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
    ) -> DocumentSummary:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        return DocumentSummary(*self._repository.document_counts(tenant_id, company_id))

    def fiscal_documents(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *,
        offset: int, limit: int, search: str | None = None,
        status: str | None = None, issued_from: date | None = None,
        issued_to: date | None = None,
    ) -> FiscalPage:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        if issued_from is not None and issued_to is not None and issued_from > issued_to:
            raise ValueError('invalid date range')
        rows, total = self._repository.list_fiscal_documents(
            tenant_id, company_id, offset=offset, limit=limit, search=search,
            status=status, issued_from=issued_from, issued_to=issued_to,
        )
        return FiscalPage(tuple(_fiscal_view(row) for row in rows), total, offset, limit)

    def fiscal_document(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        fiscal_document_id: UUID, *, item_limit: int = 200,
    ) -> FiscalDetail:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        row = self._repository.get_fiscal_document(tenant_id, company_id, fiscal_document_id)
        if row is None:
            raise OperationalUnavailableError()
        items, total = self._repository.list_fiscal_items(
            tenant_id, company_id, fiscal_document_id, limit=item_limit,
        )
        return FiscalDetail(
            _fiscal_view(row), tuple(FiscalItemView(
                item.id, item.sequence, item.product_code, item.description,
                item.ncm, item.cfop, item.commercial_unit, item.quantity,
                item.unit_value, item.gross_total, item.discount_total,
                item.other_total, item.included_in_total,
            ) for item in items), total,
            self._repository.fiscal_tax_totals(tenant_id, company_id, fiscal_document_id),
        )

    def bank_statements(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *,
        offset: int, limit: int,
    ) -> BankStatementPage:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        rows, total = self._repository.list_bank_statements(
            tenant_id, company_id, offset=offset, limit=limit,
        )
        return BankStatementPage(tuple(_statement_view(row) for row in rows), total, offset, limit)

    def bank_statement(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        statement_id: UUID, *, offset: int, limit: int, search: str | None = None,
        direction: str | None = None, posted_from: date | None = None,
        posted_to: date | None = None,
    ) -> BankStatementDetail:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        if posted_from is not None and posted_to is not None and posted_from > posted_to:
            raise ValueError('invalid date range')
        statement = self._repository.get_bank_statement(tenant_id, company_id, statement_id)
        if statement is None:
            raise OperationalUnavailableError()
        rows, total = self._repository.list_bank_transactions(
            tenant_id, company_id, statement_id, offset=offset, limit=limit,
            search=search, direction=direction, posted_from=posted_from,
            posted_to=posted_to,
        )
        return BankStatementDetail(_statement_view(statement), BankTransactionPage(
            tuple(BankTransactionView(
                item.id, item.bank_statement_id, item.transaction_date,
                item.posted_date, item.amount, item.direction,
                item.description, item.document_number, item.identity_kind,
            ) for item in rows), total, offset, limit,
        ))

    def import_nfe(self, command: NFeImportCommand) -> Journey:
        return self._nfe.prepare(JourneyCommand(
            command.tenant_id, command.company_id, command.actor_id,
            command.idempotency_key, command.accounting_date,
            command.period_start, command.period_end,
            command.approval_expires_at,
        ), content=command.content, filename=command.filename,
            correlation_id=command.correlation_id)

    def import_ofx(self, command: OfxImportCommand) -> OfxImportResult:
        context = IntakeContext(
            command.tenant_id, command.company_id, command.actor_id,
            AuditOrigin.HUMAN, command.correlation_id,
        )
        batch = self._intake.start_batch(
            context, StartBatchRequest('OFX_OPERATIONAL', command.idempotency_key),
        )
        existing_hash = self._repository.batch_content_hash(
            command.tenant_id, command.company_id, batch.id,
        )
        supplied_hash = sha256(command.content).hexdigest()
        if existing_hash is not None and existing_hash != supplied_hash:
            raise OperationalConflictError('idempotency content conflict')
        return self._ofx.import_ofx(context, OfxImportRequest(
            batch.id, command.content, command.filename,
            external_key=command.idempotency_key,
        ))

    def processing(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, batch_id: UUID,
    ) -> ProcessingView:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        batch = self._repository.get_batch(tenant_id, company_id, batch_id)
        if batch is not None:
            return _processing(batch)
        journey = self._repository.get_journey(tenant_id, company_id, batch_id)
        if journey is not None:
            return ProcessingView(
                journey.id, 'JOURNEY', 'NFE55', journey.status, 1, 1,
                1 if journey.imported.status == 'IDEMPOTENT_REDELIVERY' else 0,
                1 if journey.status == 'QUARANTINED' else 0,
                None, None, journey.version,
            )
        raise OperationalUnavailableError()

    def reviews(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *, limit: int,
    ) -> tuple[ReviewSummary, ...]:
        self._require(tenant_id, company_id, actor_id, 'journal.read')
        return tuple(
            summary for journey in self._repository.list_journeys(
                tenant_id, company_id, limit=limit,
            ) if (summary := _review_summary(journey)) is not None
        )

    def review(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, journey_id: UUID,
    ) -> ReviewDetail:
        self._require(tenant_id, company_id, actor_id, 'journal.read')
        journey = self._repository.get_journey(tenant_id, company_id, journey_id)
        if journey is None:
            raise OperationalUnavailableError()
        summary = _review_summary(journey)
        if summary is None or journey.plan is None:
            raise OperationalUnavailableError()
        accounts = {item.id: item for item in journey.plan.accounts}
        lines = tuple(ReviewLineView(
            line.account_version_id,
            accounts[line.account_version_id].code,
            accounts[line.account_version_id].name,
            line.debit, line.credit,
        ) for line in journey.lines)
        return ReviewDetail(
            summary, journey.proposer_id, journey.validation_status,
            lines, len(journey.sources),
        )

    def accounting_proposals(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *,
        offset: int, limit: int, status: str | None = None,
    ) -> AccountingProposalPage:
        self._require(tenant_id, company_id, actor_id, 'journal.read')
        rows, total = self._repository.list_proposal_journeys(
            tenant_id, company_id, offset=offset, limit=limit, status=status,
        )
        return AccountingProposalPage(tuple(
            self._proposal_summary(tenant_id, company_id, journey) for journey in rows
        ), total, offset, limit)

    def accounting_proposal(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, journey_id: UUID,
    ) -> AccountingProposalDetail:
        self._require(tenant_id, company_id, actor_id, 'journal.read')
        journey = self._repository.get_journey(tenant_id, company_id, journey_id)
        if journey is None or not _has_accounting_proposal(journey):
            raise OperationalUnavailableError()
        summary = self._proposal_summary(tenant_id, company_id, journey)
        rule = _journey_rule(journey, summary.rule_name)
        accounts = {item.id: item for item in journey.plan.accounts}
        lines = tuple(ReviewLineView(
            line.account_version_id, accounts[line.account_version_id].code,
            accounts[line.account_version_id].name, line.debit, line.credit,
        ) for line in journey.lines)
        sources = []
        for source in journey.sources:
            fiscal = self._repository.get_fiscal_document(
                tenant_id, company_id, source.source_id,
            ) if source.source_type == 'FiscalDocument' else None
            sources.append(AccountingSourceEvidence(
                source.source_type, source.source_id,
                fiscal.receipt_id if fiscal else None,
                fiscal.document_number if fiscal else None,
                fiscal.issuer_name if fiscal else None,
                fiscal.issued_at if fiscal else None,
                fiscal.invoice_total if fiscal else None,
            ))
        locks = tuple(AccountingLockView(
            record.lock.id, record.lock.scope.value,
            tuple(operation.value for operation in record.lock.operations),
            record.lock.reason, _lock_target(record.lock), record.created_at,
        ) for record in self._repository.list_active_lock_records(tenant_id, company_id)
            if _blocks_accounting_decision(record.lock, journey))
        return AccountingProposalDetail(summary, rule, lines, tuple(sources), locks)

    def accounting_catalog(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        *, at: date,
    ) -> AccountingCatalogView:
        self._require(tenant_id, company_id, actor_id, 'catalog.review')
        record = self._repository.published_catalog(
            tenant_id, company_id, at=at,
        )
        if record is None:
            raise OperationalUnavailableError()
        return _catalog_view(record)

    def accounting_rule(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, rule_id: UUID,
        *, at: date,
    ) -> AccountingRuleView:
        catalog = self.accounting_catalog(tenant_id, company_id, actor_id, at=at)
        item = next((rule for rule in catalog.rules if rule.id == rule_id), None)
        if item is None:
            raise OperationalUnavailableError()
        return item

    def accounting_account(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, account_id: UUID,
        *, at: date,
    ) -> AccountingAccountView:
        catalog = self.accounting_catalog(tenant_id, company_id, actor_id, at=at)
        item = next((account for account in catalog.accounts if account.id == account_id), None)
        if item is None:
            raise OperationalUnavailableError()
        return item

    def proposal_activity(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, journey_id: UUID,
        *, limit: int,
    ) -> tuple[AuditView, ...]:
        self._require(tenant_id, company_id, actor_id, 'journal.read')
        journey = self._repository.get_journey(tenant_id, company_id, journey_id)
        if journey is None or not _has_accounting_proposal(journey):
            raise OperationalUnavailableError()
        self._require(tenant_id, company_id, actor_id, 'audit.read')
        return tuple(AuditView(
            item.id, item.actor_id, item.origin.value, item.module, item.action,
            item.subject_type, item.subject_id, item.subject_version,
            item.correlation_id, item.occurred_at, self._audit.verify_integrity(item),
        ) for item in self._repository.list_audit_events_by_correlation(
            tenant_id, company_id, journey.correlation_id, limit=limit,
        ))

    def _proposal_summary(
        self, tenant_id: UUID, company_id: UUID, journey: Journey,
    ) -> AccountingProposalSummary:
        if not _has_accounting_proposal(journey):
            raise OperationalUnavailableError()
        source = journey.sources[0]
        fiscal = self._repository.get_fiscal_document(
            tenant_id, company_id, source.source_id,
        ) if source.source_type == 'FiscalDocument' else None
        rule_id = UUID(journey.evaluation.proposal['rule_version_id'])
        return AccountingProposalSummary(
            journey.id, journey.company_id, journey.version, journey.status,
            journey.proposal.id, journey.revision.id, journey.revision_hash,
            journey.revision.accounting_date,
            source.source_type, source.source_id,
            fiscal.receipt_id if fiscal else None, rule_id,
            self._repository.rule_name(tenant_id, company_id, rule_id),
            sum((line.debit for line in journey.lines), Decimal('0')),
            sum((line.credit for line in journey.lines), Decimal('0')),
            sum((line.debit for line in journey.lines), Decimal('0'))
            == sum((line.credit for line in journey.lines), Decimal('0')),
            journey.validation_status, journey.proposer_id,
            journey.plan.approval_role, journey.plan.responsible_role,
            journey.request.expires_at if journey.request else None,
            journey.decision.actor_id if journey.decision else None,
            journey.decision.decided_at if journey.decision else None,
        )

    def decide(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        correlation_id: UUID, journey_id: UUID, *, expected_version: int,
        revision_id: UUID, revision_hash: str, decision: str,
        idempotency_key: str,
    ) -> Journey:
        return self._nfe.record_decision(IntakeContext(
            tenant_id, company_id, actor_id, AuditOrigin.HUMAN, correlation_id,
        ), journey_id, expected_version=expected_version,
            revision_id=revision_id, revision_hash=revision_hash,
            decision=decision, idempotency_key=idempotency_key)

    def exceptions(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *, limit: int,
    ) -> tuple[ExceptionView, ...]:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        return tuple(ExceptionView(
            item.id, item.transformation_run_id, item.code, item.severity,
            item.field_path, item.rule_reference, item.resolution_status,
            item.created_at,
        ) for item in self._repository.list_issues(
            tenant_id, company_id, limit=limit,
        ))

    def audit_events(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *, limit: int,
    ) -> tuple[AuditView, ...]:
        self._require(tenant_id, company_id, actor_id, 'audit.read')
        return tuple(AuditView(
            item.id, item.actor_id, item.origin.value, item.module, item.action,
            item.subject_type, item.subject_id, item.subject_version,
            item.correlation_id, item.occurred_at,
            self._audit.verify_integrity(item),
        ) for item in self._repository.list_audit_events(
            tenant_id, company_id, limit=limit,
        ))

    def decision_line(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        root_type: DecisionLineRoot, root_id: UUID, *, limit: int,
    ) -> DecisionLine:
        return self._traceability.get(
            tenant_id, company_id, actor_id, root_type, root_id, limit=limit,
        )

    def _require(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, permission: str,
    ) -> None:
        self._authorization.require(AuthorizationRequest(
            tenant_id, actor_id, PermissionCode(permission), company_id,
        ))


def _processing(batch: ImportBatch) -> ProcessingView:
    return ProcessingView(
        batch.id, 'BATCH', batch.source, batch.status, batch.total_items,
        batch.received_items, batch.duplicate_items, batch.failed_items,
        batch.started_at, batch.completed_at, batch.revision,
    )


def _review_summary(journey: Journey) -> ReviewSummary | None:
    if journey.revision is None or journey.revision_hash is None:
        return None
    return ReviewSummary(
        journey.id, journey.version, journey.status, journey.revision.id,
        journey.revision_hash, journey.revision.accounting_date,
        journey.request.id if journey.request else None,
        journey.request.expires_at if journey.request else None,
    )


def _has_accounting_proposal(journey: Journey) -> bool:
    return bool(
        journey.proposal is not None and journey.revision is not None
        and journey.evaluation is not None and journey.evaluation.proposal is not None
        and journey.plan is not None and journey.lines and journey.sources
        and journey.revision_hash is not None
    )


def _journey_rule(journey: Journey, name: str | None) -> AccountingRuleView:
    assert journey.plan is not None and journey.evaluation is not None
    assert journey.evaluation.proposal is not None
    rule_id = UUID(journey.evaluation.proposal['rule_version_id'])
    rule = next(item for item in journey.plan.rules if item.id == rule_id)
    accounts = {item.id: item for item in journey.plan.accounts}
    debit = accounts[rule.debit_account_version_id]
    credit = accounts[rule.credit_account_version_id]
    return AccountingRuleView(
        rule.id, name, rule.scope, rule.priority, rule.status,
        rule.automation_level,
        tuple(RuleConditionView(*condition) for condition in rule.conditions),
        debit.id, debit.code, debit.name, credit.id, credit.code, credit.name,
    )


def _catalog_view(record: object) -> AccountingCatalogView:
    content = record.content
    raw_accounts = tuple(content.get('accounts', ()))
    by_id = {str(item['id']): item for item in raw_accounts}
    accounts = tuple(AccountingAccountView(
        UUID(item['id']), str(item['code']), str(item['name']),
        str(item['nature']), str(item['normal_balance']),
        bool(item['is_synthetic']), bool(item['is_postable']), str(item['status']),
    ) for item in raw_accounts)
    rules = []
    for item in content.get('rules', ()):
        debit = by_id[str(item['debit_account_version_id'])]
        credit = by_id[str(item['credit_account_version_id'])]
        rules.append(AccountingRuleView(
            UUID(item['id']), str(item.get('name') or '') or None,
            str(item['scope']), int(item['priority']), str(item['status']),
            str(item['automation_level']),
            tuple(RuleConditionView(*map(str, condition)) for condition in item['conditions']),
            UUID(debit['id']), str(debit['code']), str(debit['name']),
            UUID(credit['id']), str(credit['code']), str(credit['name']),
        ))
    mapping = content.get('mapping', {})
    mappings = []
    for item in mapping.get('entries', ()):
        target = by_id[str(item['target_account_version_id'])]
        mappings.append(AccountingMappingView(
            UUID(item['id']), str(item['key']), int(item['priority']),
            item.get('external_code'), item.get('history_contains'),
            item.get('dimension_code'), item.get('canonical_entity'),
            UUID(target['id']), str(target['code']), str(target['name']),
        ))
    posting = content.get('posting', {})
    return AccountingCatalogView(
        record.id, record.version_no, record.valid_from, record.valid_to,
        int(posting['decimal_places']), str(posting['amount_field']),
        tuple(rules), accounts, tuple(mappings),
    )


def _lock_target(lock: AccountLock) -> str:
    target = {
        'ACCOUNT': lock.account_id,
        'GROUP': lock.group_id,
        'MODULE': lock.module,
        'COMPETENCE': lock.competence,
        'EXERCISE': lock.exercise,
    }[lock.scope.value]
    return str(target)


def _blocks_accounting_decision(lock: AccountLock, journey: Journey) -> bool:
    assert journey.plan is not None and journey.revision is not None
    groups = dict(journey.plan.account_groups)
    for line in journey.lines:
        account = next(item for item in journey.plan.accounts
                       if item.id == line.account_version_id)
        try:
            validate_effect((lock,), EffectContext(
                journey.tenant_id, journey.company_id, account.account_id,
                groups.get(account.account_id, ()), 'accounting',
                journey.revision.accounting_date, EffectOperation.APPROVE,
                EffectChannel.USER,
            ))
        except AccountLockedError:
            return True
    return False


def _document_view(row: object) -> DocumentView:
    return DocumentView(
        row.id, row.company_id, row.batch_id, row.filename, row.media_type,
        row.size_bytes, row.source, row.channel, row.receipt_result,
        row.processing_status, row.error_code, row.received_at,
    )


def _fiscal_view(row: object) -> FiscalDocumentView:
    return FiscalDocumentView(
        row.id, row.company_id, row.access_key, row.model, row.schema_version,
        row.series, row.document_number, row.operation_nature,
        row.issuer_tax_id, row.issuer_name, row.recipient_tax_id,
        row.recipient_name, row.issued_at, row.movement_at,
        row.products_total, row.freight_total, row.insurance_total,
        row.discount_total, row.other_total, row.tax_total, row.invoice_total,
        row.observed_status, row.protocol_status_code,
        row.protocol_status_reason, row.created_at, row.receipt_id,
    )


def _statement_view(row: object) -> BankStatementView:
    return BankStatementView(
        row.id, row.company_id, row.bank_id, _masked(row.branch_id, visible=2),
        _masked(row.account_number, visible=4) or '••••', row.account_type,
        row.start_date, row.end_date, row.opening_balance, row.closing_balance,
        row.currency_code, row.sign_policy, row.created_at, row.receipt_id,
    )


def _masked(value: str | None, *, visible: int) -> str | None:
    if value is None:
        return None
    visible_count = min(visible, max(1, len(value) // 2))
    suffix = value[-visible_count:]
    return f'••••{suffix}'
