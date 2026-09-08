'''Comandos autenticados de governança; tenant sempre vem da identidade.'''

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from serdial21.entrypoints.http.dependencies.database import get_db_session
from serdial21.entrypoints.http.dependencies.identity import get_authenticated_principal
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuthorizationRepository,
)
from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError, AuthorizationService,
)
from serdial21.modules.audit.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.catalog.adapters.outbound.persistence.repositories import (
    SqlAlchemyProductionCatalogRepository,
)
from serdial21.modules.catalog.application.services.governance import CatalogGovernanceService
from serdial21.modules.catalog.domain.entities import (
    AccountSpec, CatalogConflictError, CatalogSpec, CatalogUnavailableError,
    MappingEntrySpec, RuleSpec, WorkflowSpec,
)
from serdial21.modules.identity.domain.entities import AuthenticatedPrincipal


router = APIRouter(prefix='/catalogs', tags=['catalog'])


class AccountInput(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    nature: str = Field(min_length=1, max_length=32)
    normal_balance: str = Field(min_length=1, max_length=16)
    parent_key: str | None = Field(default=None, max_length=100)
    is_synthetic: bool
    is_postable: bool


class RuleInput(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    scope: str = Field(min_length=1, max_length=64)
    conditions: list[tuple[str, str, str]] = Field(max_length=100)
    priority: int
    debit_account_key: str = Field(min_length=1, max_length=100)
    credit_account_key: str = Field(min_length=1, max_length=100)
    automation_level: str = Field(min_length=1, max_length=32)
    tests_passed: bool


class MappingInput(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    priority: int
    target_account_key: str = Field(min_length=1, max_length=100)
    external_code: str | None = Field(default=None, max_length=200)
    history_contains: str | None = Field(default=None, max_length=500)
    dimension_code: str | None = Field(default=None, max_length=100)
    canonical_entity: str | None = Field(default=None, max_length=100)


class WorkflowInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    approval_role: str = Field(min_length=1, max_length=100)
    responsible_role: str = Field(min_length=1, max_length=100)


class CatalogDraftRequest(BaseModel):
    company_id: UUID
    name: str = Field(min_length=1, max_length=200)
    ledger_name: str = Field(min_length=1, max_length=200)
    currency_code: str = Field(min_length=3, max_length=3)
    chart_name: str = Field(min_length=1, max_length=200)
    accounts: list[AccountInput] = Field(min_length=1, max_length=10_000)
    rules: list[RuleInput] = Field(min_length=1, max_length=10_000)
    mapping_name: str = Field(min_length=1, max_length=200)
    mapping_namespace: str = Field(min_length=1, max_length=100)
    mappings: list[MappingInput] = Field(max_length=10_000)
    workflow: WorkflowInput
    amount_field: str = Field(min_length=1, max_length=100)
    decimal_places: int = Field(ge=0, le=6)
    valid_from: date
    valid_to: date | None = None
    reason: str = Field(min_length=1, max_length=500)


class CatalogTransitionRequest(BaseModel):
    company_id: UUID
    reason: str = Field(min_length=1, max_length=500)


class CatalogVersionResponse(BaseModel):
    id: UUID
    catalog_id: UUID
    supersedes_version_id: UUID | None
    version_no: int
    status: str
    content_hash: str


SessionDependency = Annotated[Session, Depends(get_db_session)]
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_authenticated_principal)]


@router.post('', response_model=CatalogVersionResponse, status_code=201)
def create_draft(
    payload: CatalogDraftRequest, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> CatalogVersionResponse:
    service = _service(session)
    try:
        version = service.create_draft(
            principal.identity.tenant_id, payload.company_id, principal.user_id,
            _spec(payload), correlation_id=UUID(request.state.correlation_id),
            reason=payload.reason,
        )
    except (AccessDeniedError, CatalogUnavailableError, PermissionError):
        _deny()
    except (CatalogConflictError, IntegrityError):
        session.rollback()
        _conflict()
    except ValueError:
        _invalid()
    return _response(version)


@router.post('/versions/{published_version_id}/next', response_model=CatalogVersionResponse, status_code=201)
def create_next_draft(
    published_version_id: UUID, payload: CatalogDraftRequest, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> CatalogVersionResponse:
    try:
        version = _service(session).create_next_draft(
            principal.identity.tenant_id, payload.company_id, principal.user_id,
            published_version_id, _spec(payload),
            correlation_id=UUID(request.state.correlation_id), reason=payload.reason,
        )
    except (AccessDeniedError, CatalogUnavailableError, PermissionError):
        _deny()
    except (CatalogConflictError, IntegrityError):
        session.rollback()
        _conflict()
    except ValueError:
        _invalid()
    return _response(version)


@router.post('/versions/{version_id}/review', response_model=CatalogVersionResponse)
def submit_review(
    version_id: UUID, payload: CatalogTransitionRequest, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> CatalogVersionResponse:
    try:
        version = _service(session).submit_review(
            principal.identity.tenant_id, payload.company_id, principal.user_id,
            version_id, correlation_id=UUID(request.state.correlation_id),
            reason=payload.reason,
        )
    except (AccessDeniedError, CatalogUnavailableError, PermissionError):
        _deny()
    except CatalogConflictError:
        _conflict()
    except ValueError:
        _conflict()
    return _response(version)


@router.post('/versions/{version_id}/publish', response_model=CatalogVersionResponse)
def publish(
    version_id: UUID, payload: CatalogTransitionRequest, request: Request,
    principal: PrincipalDependency, session: SessionDependency,
) -> CatalogVersionResponse:
    try:
        version = _service(session).publish(
            principal.identity.tenant_id, payload.company_id, principal.user_id,
            version_id, correlation_id=UUID(request.state.correlation_id),
            reason=payload.reason,
        )
    except (AccessDeniedError, CatalogUnavailableError, PermissionError):
        _deny()
    except CatalogConflictError:
        _conflict()
    except ValueError:
        _conflict()
    return _response(version)


def _service(session: Session) -> CatalogGovernanceService:
    return CatalogGovernanceService(
        SqlAlchemyProductionCatalogRepository(session),
        AuthorizationService(SqlAlchemyAuthorizationRepository(session)),
        AuditService(SqlAlchemyAuditRepository(session)),
    )


def _spec(payload: CatalogDraftRequest) -> CatalogSpec:
    return CatalogSpec(
        payload.name, payload.ledger_name, payload.currency_code,
        payload.chart_name,
        tuple(AccountSpec(**item.model_dump()) for item in payload.accounts),
        tuple(RuleSpec(
            **(item.model_dump() | {'conditions': tuple(item.conditions)})
        ) for item in payload.rules),
        payload.mapping_name, payload.mapping_namespace,
        tuple(MappingEntrySpec(**item.model_dump()) for item in payload.mappings),
        WorkflowSpec(**payload.workflow.model_dump()),
        payload.amount_field, payload.decimal_places,
        payload.valid_from, payload.valid_to,
    )


def _response(version: object) -> CatalogVersionResponse:
    return CatalogVersionResponse.model_validate(version, from_attributes=True)


def _deny() -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='access denied')


def _conflict() -> None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='catalog conflict')


def _invalid() -> None:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail='invalid catalog specification')
