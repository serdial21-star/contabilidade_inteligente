'''Borda operacional autenticada, fina e sem regra contábil.'''

from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePath
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from serdial21.bootstrap.operations import create_operational_runtime
from serdial21.bootstrap.settings import AppSettings
from serdial21.entrypoints.http.dependencies.database import get_db_session
from serdial21.entrypoints.http.dependencies.identity import get_authenticated_principal
from serdial21.modules.access_control.application.services.authorization import AccessDeniedError
from serdial21.modules.identity.domain.entities import AuthenticatedPrincipal
from serdial21.modules.intake_documents.application.services.intake import (
    IntakeResourceUnavailableError, UploadTooLargeError,
)
from serdial21.modules.locks.domain.entities import AccountLockedError
from serdial21.modules.operations.application.services.operations import (
    NFeImportCommand, OfxImportCommand, OperationalConflictError,
    OperationalUnavailableError,
)
from serdial21.modules.workflow.application.journey import (
    JourneyConflictError, JourneyNotReadyError, JourneyUnavailableError,
)


router = APIRouter(prefix='/operations/companies/{company_id}', tags=['operations'])


class ImportResponse(BaseModel):
    resource_id: UUID
    resource_kind: Literal['JOURNEY', 'BATCH']
    status: str
    version: int | None = None
    transformation_run_id: UUID | None = None
    duplicate_items: int = 0


class ProcessingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class ReviewSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    journey_id: UUID
    version: int
    status: str
    revision_id: UUID
    revision_hash: str
    accounting_date: date
    request_id: UUID | None
    expires_at: datetime | None


class ReviewLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    account_version_id: UUID
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal


class ReviewDetailResponse(BaseModel):
    summary: ReviewSummaryResponse
    proposer_id: UUID
    validation_status: str | None
    lines: list[ReviewLineResponse]
    source_count: int


class DecisionRequest(BaseModel):
    expected_version: int = Field(ge=1)
    revision_id: UUID
    revision_hash: str = Field(min_length=64, max_length=64, pattern=r'^[0-9a-f]{64}$')


class DecisionResponse(BaseModel):
    journey_id: UUID
    version: int
    status: str
    decision_id: UUID


class ExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    transformation_run_id: UUID
    code: str
    severity: str
    field_path: str | None
    rule_reference: str | None
    resolution_status: str
    created_at: datetime


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    legal_name: str
    trade_name: str | None
    tax_identifier: str
    status: str
    timezone: str
    currency_code: str


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class DocumentPageResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    offset: int
    limit: int


class DocumentDetailResponse(BaseModel):
    document: DocumentResponse
    issues: list[ExceptionResponse]
    fiscal_document_id: UUID | None
    bank_statement_id: UUID | None


class DocumentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    received: int
    processed: int
    attention_required: int


class FiscalDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class FiscalItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class FiscalPageResponse(BaseModel):
    items: list[FiscalDocumentResponse]
    total: int
    offset: int
    limit: int


class TaxTotalResponse(BaseModel):
    tax_type: str
    amount: Decimal


class FiscalDetailResponse(BaseModel):
    document: FiscalDocumentResponse
    items: list[FiscalItemResponse]
    item_count: int
    tax_totals: list[TaxTotalResponse]


class BankStatementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class BankStatementPageResponse(BaseModel):
    items: list[BankStatementResponse]
    total: int
    offset: int
    limit: int


class BankTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    bank_statement_id: UUID
    transaction_date: date | None
    posted_date: date | None
    amount: Decimal
    direction: str
    description: str | None
    document_number: str | None
    identity_kind: str


class BankTransactionPageResponse(BaseModel):
    items: list[BankTransactionResponse]
    total: int
    offset: int
    limit: int


class BankStatementDetailResponse(BaseModel):
    statement: BankStatementResponse
    transactions: BankTransactionPageResponse


class AccountingProposalSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class AccountingProposalPageResponse(BaseModel):
    items: list[AccountingProposalSummaryResponse]
    total: int
    offset: int
    limit: int


class RuleConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    field: str
    operator: str
    value: str


class AccountingRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str | None
    scope: str
    priority: int
    status: str
    automation_level: str
    conditions: list[RuleConditionResponse]
    debit_account_version_id: UUID
    debit_account_code: str
    debit_account_name: str
    credit_account_version_id: UUID
    credit_account_code: str
    credit_account_name: str


class AccountingSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source_type: str
    source_id: UUID
    document_receipt_id: UUID | None
    document_number: str | None
    issuer_name: str | None
    issued_at: datetime | None
    amount: Decimal | None


class AccountingLockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    scope: str
    operations: list[str]
    reason: str
    target: str
    created_at: datetime


class AccountingProposalDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    summary: AccountingProposalSummaryResponse
    rule: AccountingRuleResponse
    lines: list[ReviewLineResponse]
    sources: list[AccountingSourceResponse]
    active_locks: list[AccountingLockResponse]


class AccountingAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    nature: str
    normal_balance: str
    is_synthetic: bool
    is_postable: bool
    status: str


class AccountingMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class AccountingCatalogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    version_id: UUID
    version_no: int
    valid_from: date
    valid_to: date | None
    decimal_places: int
    amount_field: str
    rules: list[AccountingRuleResponse]
    accounts: list[AccountingAccountResponse]
    mappings: list[AccountingMappingResponse]


SessionDependency = Annotated[Session, Depends(get_db_session)]
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_authenticated_principal)]
IdempotencyKey = Annotated[str, Header(alias='Idempotency-Key', min_length=1, max_length=128)]
Filename = Annotated[str, Header(alias='X-Filename', min_length=1, max_length=255)]


@router.get('', response_model=CompanyResponse)
def company_detail(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency,
) -> CompanyResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).company(
            principal.identity.tenant_id, company_id, principal.user_id,
        )
    except Exception as error:
        _map_error(session, error)
    return CompanyResponse.model_validate(item)


@router.get('/documents', response_model=DocumentPageResponse)
def documents(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    document_status: Annotated[str | None, Query(alias='status', min_length=1, max_length=32)] = None,
    source: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    received_from: date | None = None, received_to: date | None = None,
) -> DocumentPageResponse:
    try:
        page = create_operational_runtime(session, request.app.state.settings).documents(
            principal.identity.tenant_id, company_id, principal.user_id,
            offset=offset, limit=limit, search=search, status=document_status,
            source=source, received_from=received_from, received_to=received_to,
        )
    except Exception as error:
        _map_error(session, error)
    return DocumentPageResponse(
        items=[DocumentResponse.model_validate(item) for item in page.items],
        total=page.total, offset=page.offset, limit=page.limit,
    )


@router.get('/documents/summary', response_model=DocumentSummaryResponse)
def document_summary(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency,
) -> DocumentSummaryResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).document_summary(
            principal.identity.tenant_id, company_id, principal.user_id,
        )
    except Exception as error:
        _map_error(session, error)
    return DocumentSummaryResponse.model_validate(item)


@router.get('/documents/{document_id}', response_model=DocumentDetailResponse)
def document_detail(
    company_id: UUID, document_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> DocumentDetailResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).document(
            principal.identity.tenant_id, company_id, principal.user_id, document_id,
        )
    except Exception as error:
        _map_error(session, error)
    return DocumentDetailResponse(
        document=DocumentResponse.model_validate(item.document),
        issues=[ExceptionResponse.model_validate(issue) for issue in item.issues],
        fiscal_document_id=item.fiscal_document_id,
        bank_statement_id=item.bank_statement_id,
    )


@router.get('/fiscal-documents', response_model=FiscalPageResponse)
def fiscal_documents(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    fiscal_status: Annotated[str | None, Query(alias='status', min_length=1, max_length=32)] = None,
    issued_from: date | None = None, issued_to: date | None = None,
) -> FiscalPageResponse:
    try:
        page = create_operational_runtime(session, request.app.state.settings).fiscal_documents(
            principal.identity.tenant_id, company_id, principal.user_id,
            offset=offset, limit=limit, search=search, status=fiscal_status,
            issued_from=issued_from, issued_to=issued_to,
        )
    except Exception as error:
        _map_error(session, error)
    return FiscalPageResponse(
        items=[FiscalDocumentResponse.model_validate(item) for item in page.items],
        total=page.total, offset=page.offset, limit=page.limit,
    )


@router.get('/fiscal-documents/{fiscal_document_id}', response_model=FiscalDetailResponse)
def fiscal_document_detail(
    company_id: UUID, fiscal_document_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> FiscalDetailResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).fiscal_document(
            principal.identity.tenant_id, company_id, principal.user_id,
            fiscal_document_id,
        )
    except Exception as error:
        _map_error(session, error)
    return FiscalDetailResponse(
        document=FiscalDocumentResponse.model_validate(item.document),
        items=[FiscalItemResponse.model_validate(row) for row in item.items],
        item_count=item.item_count,
        tax_totals=[TaxTotalResponse(tax_type=tax_type, amount=amount) for tax_type, amount in item.tax_totals],
    )


@router.get('/bank-statements', response_model=BankStatementPageResponse)
def bank_statements(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> BankStatementPageResponse:
    try:
        page = create_operational_runtime(session, request.app.state.settings).bank_statements(
            principal.identity.tenant_id, company_id, principal.user_id,
            offset=offset, limit=limit,
        )
    except Exception as error:
        _map_error(session, error)
    return BankStatementPageResponse(
        items=[BankStatementResponse.model_validate(item) for item in page.items],
        total=page.total, offset=page.offset, limit=page.limit,
    )


@router.get('/bank-statements/{statement_id}', response_model=BankStatementDetailResponse)
def bank_statement_detail(
    company_id: UUID, statement_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    direction: Literal['CREDIT', 'DEBIT'] | None = None,
    posted_from: date | None = None, posted_to: date | None = None,
) -> BankStatementDetailResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).bank_statement(
            principal.identity.tenant_id, company_id, principal.user_id,
            statement_id, offset=offset, limit=limit, search=search,
            direction=direction, posted_from=posted_from, posted_to=posted_to,
        )
    except Exception as error:
        _map_error(session, error)
    return BankStatementDetailResponse(
        statement=BankStatementResponse.model_validate(item.statement),
        transactions=BankTransactionPageResponse(
            items=[BankTransactionResponse.model_validate(row) for row in item.transactions.items],
            total=item.transactions.total, offset=item.transactions.offset,
            limit=item.transactions.limit,
        ),
    )


@router.get('/accounting-proposals', response_model=AccountingProposalPageResponse)
def accounting_proposals(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    proposal_status: Annotated[
        Literal['PENDING_APPROVAL', 'APPROVED', 'REJECTED',
                'BLOCKED_FOR_HOMOLOGATION', 'SUPERSEDED'] | None,
        Query(alias='status'),
    ] = None,
) -> AccountingProposalPageResponse:
    try:
        page = create_operational_runtime(session, request.app.state.settings).accounting_proposals(
            principal.identity.tenant_id, company_id, principal.user_id,
            offset=offset, limit=limit, status=proposal_status,
        )
    except Exception as error:
        _map_error(session, error)
    return AccountingProposalPageResponse(
        items=[AccountingProposalSummaryResponse.model_validate(item) for item in page.items],
        total=page.total, offset=page.offset, limit=page.limit,
    )


@router.get('/accounting-proposals/{journey_id}', response_model=AccountingProposalDetailResponse)
def accounting_proposal_detail(
    company_id: UUID, journey_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> AccountingProposalDetailResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).accounting_proposal(
            principal.identity.tenant_id, company_id, principal.user_id, journey_id,
        )
    except Exception as error:
        _map_error(session, error)
    return AccountingProposalDetailResponse.model_validate(item)


@router.get('/accounting-proposals/{journey_id}/activity', response_model=list[AuditResponse])
def accounting_proposal_activity(
    company_id: UUID, journey_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[AuditResponse]:
    try:
        items = create_operational_runtime(session, request.app.state.settings).proposal_activity(
            principal.identity.tenant_id, company_id, principal.user_id,
            journey_id, limit=limit,
        )
    except Exception as error:
        _map_error(session, error)
    return [AuditResponse.model_validate(item) for item in items]


@router.get('/accounting-catalog', response_model=AccountingCatalogResponse)
def accounting_catalog(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, effective_at: date,
) -> AccountingCatalogResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).accounting_catalog(
            principal.identity.tenant_id, company_id, principal.user_id, at=effective_at,
        )
    except Exception as error:
        _map_error(session, error)
    return AccountingCatalogResponse.model_validate(item)


@router.get('/accounting-rules/{rule_id}', response_model=AccountingRuleResponse)
def accounting_rule_detail(
    company_id: UUID, rule_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency, effective_at: date,
) -> AccountingRuleResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).accounting_rule(
            principal.identity.tenant_id, company_id, principal.user_id, rule_id,
            at=effective_at,
        )
    except Exception as error:
        _map_error(session, error)
    return AccountingRuleResponse.model_validate(item)


@router.get('/accounting-accounts/{account_id}', response_model=AccountingAccountResponse)
def accounting_account_detail(
    company_id: UUID, account_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency, effective_at: date,
) -> AccountingAccountResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).accounting_account(
            principal.identity.tenant_id, company_id, principal.user_id, account_id,
            at=effective_at,
        )
    except Exception as error:
        _map_error(session, error)
    return AccountingAccountResponse.model_validate(item)


@router.post('/imports/nfe', response_model=ImportResponse, status_code=202)
async def import_nfe(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, idempotency_key: IdempotencyKey,
    filename: Filename, accounting_date: Annotated[date, Query()],
    period_start: Annotated[date, Query()], period_end: Annotated[date, Query()],
    approval_expires_at: Annotated[datetime, Query()],
) -> ImportResponse:
    _validate_file(filename, '.xml')
    _validate_media(request, {'application/xml', 'text/xml'})
    settings: AppSettings = request.app.state.settings
    content = await _read_limited(request, settings.nfe_max_xml_bytes)
    try:
        journey = create_operational_runtime(session, settings).import_nfe(NFeImportCommand(
            principal.identity.tenant_id, company_id, principal.user_id,
            idempotency_key, accounting_date, period_start, period_end,
            approval_expires_at,
            content, filename, UUID(request.state.correlation_id),
        ))
    except Exception as error:
        _map_error(session, error)
    return ImportResponse(
        resource_id=journey.id, resource_kind='JOURNEY', status=journey.status,
        version=journey.version,
        transformation_run_id=journey.imported.transformation_run_id,
        duplicate_items=(1 if journey.imported.status == 'IDEMPOTENT_REDELIVERY' else 0),
    )


@router.post('/imports/ofx', response_model=ImportResponse, status_code=202)
async def import_ofx(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, idempotency_key: IdempotencyKey,
    filename: Filename,
) -> ImportResponse:
    _validate_file(filename, '.ofx')
    _validate_media(request, {'application/x-ofx', 'application/ofx', 'text/plain'})
    settings: AppSettings = request.app.state.settings
    content = await _read_limited(request, settings.document_max_upload_bytes)
    try:
        service = create_operational_runtime(session, settings)
        result = service.import_ofx(OfxImportCommand(
            principal.identity.tenant_id, company_id, principal.user_id,
            idempotency_key, content, filename,
            UUID(request.state.correlation_id),
        ))
        batch_id = _batch_id_for_result(session, result.receipt_id)
    except Exception as error:
        _map_error(session, error)
    return ImportResponse(
        resource_id=batch_id, resource_kind='BATCH', status=result.status,
        transformation_run_id=result.transformation_run_id,
        duplicate_items=result.duplicate_transactions,
    )


@router.get('/processing/{resource_id}', response_model=ProcessingResponse)
def processing(
    company_id: UUID, resource_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> ProcessingResponse:
    try:
        view = create_operational_runtime(session, request.app.state.settings).processing(
            principal.identity.tenant_id, company_id, principal.user_id, resource_id,
        )
    except Exception as error:
        _map_error(session, error)
    return ProcessingResponse.model_validate(view)


@router.get('/reviews', response_model=list[ReviewSummaryResponse])
def reviews(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ReviewSummaryResponse]:
    try:
        result = create_operational_runtime(session, request.app.state.settings).reviews(
            principal.identity.tenant_id, company_id, principal.user_id, limit=limit,
        )
    except Exception as error:
        _map_error(session, error)
    return [ReviewSummaryResponse.model_validate(item) for item in result]


@router.get('/reviews/{journey_id}', response_model=ReviewDetailResponse)
def review(
    company_id: UUID, journey_id: UUID, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> ReviewDetailResponse:
    try:
        item = create_operational_runtime(session, request.app.state.settings).review(
            principal.identity.tenant_id, company_id, principal.user_id, journey_id,
        )
    except Exception as error:
        _map_error(session, error)
    return ReviewDetailResponse(
        summary=ReviewSummaryResponse.model_validate(item.summary),
        proposer_id=item.proposer_id, validation_status=item.validation_status,
        lines=[ReviewLineResponse.model_validate(line) for line in item.lines],
        source_count=item.source_count,
    )


@router.post('/reviews/{journey_id}/approve', response_model=DecisionResponse)
def approve(
    company_id: UUID, journey_id: UUID, payload: DecisionRequest,
    request: Request, principal: PrincipalDependency, session: SessionDependency,
    idempotency_key: IdempotencyKey,
) -> DecisionResponse:
    return _decision(
        company_id, journey_id, payload, 'APPROVED', idempotency_key, request, principal, session,
    )


@router.post('/reviews/{journey_id}/reject', response_model=DecisionResponse)
def reject(
    company_id: UUID, journey_id: UUID, payload: DecisionRequest,
    request: Request, principal: PrincipalDependency, session: SessionDependency,
    idempotency_key: IdempotencyKey,
) -> DecisionResponse:
    return _decision(
        company_id, journey_id, payload, 'REJECTED', idempotency_key, request, principal, session,
    )


@router.get('/exceptions', response_model=list[ExceptionResponse])
def exceptions(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ExceptionResponse]:
    try:
        result = create_operational_runtime(session, request.app.state.settings).exceptions(
            principal.identity.tenant_id, company_id, principal.user_id, limit=limit,
        )
    except Exception as error:
        _map_error(session, error)
    return [ExceptionResponse.model_validate(item) for item in result]


@router.get('/audit-events', response_model=list[AuditResponse])
def audit_events(
    company_id: UUID, request: Request, principal: PrincipalDependency,
    session: SessionDependency, limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AuditResponse]:
    try:
        result = create_operational_runtime(session, request.app.state.settings).audit_events(
            principal.identity.tenant_id, company_id, principal.user_id, limit=limit,
        )
    except Exception as error:
        _map_error(session, error)
    return [AuditResponse.model_validate(item) for item in result]


def _decision(
    company_id: UUID, journey_id: UUID, payload: DecisionRequest, decision: str,
    idempotency_key: str, request: Request, principal: AuthenticatedPrincipal, session: Session,
) -> DecisionResponse:
    try:
        journey = create_operational_runtime(session, request.app.state.settings).decide(
            principal.identity.tenant_id, company_id, principal.user_id,
            UUID(request.state.correlation_id), journey_id,
            expected_version=payload.expected_version,
            revision_id=payload.revision_id, revision_hash=payload.revision_hash,
            decision=decision, idempotency_key=idempotency_key,
        )
    except Exception as error:
        _map_error(session, error)
    assert journey.decision is not None
    return DecisionResponse(
        journey_id=journey.id, version=journey.version,
        status=journey.status, decision_id=journey.decision.id,
    )


async def _read_limited(request: Request, limit: int) -> bytes:
    raw_length = request.headers.get('content-length')
    if raw_length is not None:
        try:
            if int(raw_length) > limit:
                _too_large()
        except ValueError:
            raise HTTPException(status_code=400, detail='invalid content length') from None
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > limit:
            _too_large()
    if not content:
        raise HTTPException(status_code=422, detail='invalid file')
    return bytes(content)


def _validate_file(filename: str, extension: str) -> None:
    if PurePath(filename).name != filename or not filename.lower().endswith(extension):
        raise HTTPException(status_code=422, detail='invalid file')


def _validate_media(request: Request, allowed: set[str]) -> None:
    media_type = request.headers.get('content-type', '').split(';', 1)[0].strip().lower()
    if media_type not in allowed:
        raise HTTPException(status_code=415, detail='unsupported media type')


def _batch_id_for_result(session: Session, receipt_id: UUID) -> UUID:
    from sqlalchemy import select
    from serdial21.modules.intake_documents.adapters.outbound.persistence.models import ArtifactReceiptModel
    session.flush()
    batch_id = session.scalar(select(ArtifactReceiptModel.batch_id).where(
        ArtifactReceiptModel.id == receipt_id,
    ))
    if batch_id is None:
        raise OperationalUnavailableError()
    return batch_id


def _map_error(session: Session, error: Exception) -> None:
    if isinstance(error, AccountLockedError):
        session.rollback()
        raise HTTPException(status_code=423, detail='operation locked') from None
    if isinstance(error, AccessDeniedError):
        raise HTTPException(status_code=403, detail='access denied') from None
    if isinstance(error, PermissionError):
        raise HTTPException(status_code=403, detail='access denied') from None
    if isinstance(error, (OperationalUnavailableError, JourneyUnavailableError,
                          IntakeResourceUnavailableError)):
        raise HTTPException(status_code=404, detail='resource unavailable') from None
    if isinstance(error, (OperationalConflictError, JourneyConflictError,
                          JourneyNotReadyError, IntegrityError)):
        session.rollback()
        raise HTTPException(status_code=409, detail='operation conflict') from None
    if isinstance(error, UploadTooLargeError):
        _too_large()
    if isinstance(error, ValueError):
        raise HTTPException(status_code=422, detail='invalid operation') from None
    raise error


def _too_large() -> None:
    raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail='payload too large')
