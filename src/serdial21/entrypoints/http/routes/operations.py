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


SessionDependency = Annotated[Session, Depends(get_db_session)]
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_authenticated_principal)]
IdempotencyKey = Annotated[str, Header(alias='Idempotency-Key', min_length=1, max_length=128)]
Filename = Annotated[str, Header(alias='X-Filename', min_length=1, max_length=255)]


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
    if isinstance(error, AccessDeniedError):
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
