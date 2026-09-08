'''Borda mínima de identidade; IDs são seletores, nunca autoridade.'''

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.settings import AppSettings
from serdial21.entrypoints.http.dependencies.database import get_db_session
from serdial21.entrypoints.http.dependencies.identity import get_authenticated_principal
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuthorizationRepository,
)
from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError,
    AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.identity.adapters.outbound.persistence.repositories import (
    SqlAlchemyIdentityDirectory,
    SqlAlchemyIdentityLifecycleRepository,
)
from serdial21.modules.identity.application.services.authentication import IdentityContextService
from serdial21.modules.identity.application.services.lifecycle import (
    IdentityLifecycleConflictError,
    IdentityLifecycleDeniedError,
    IdentityLifecycleService,
    OnboardIdentity,
)
from serdial21.modules.identity.domain.entities import AuthenticatedPrincipal


router = APIRouter(prefix='/identity', tags=['identity'])


class IdentityContextResponse(BaseModel):
    tenant_id: UUID
    user_id: UUID
    membership_id: UUID
    company_id: UUID
    permission: str


class OnboardingRequest(BaseModel):
    provider_subject: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    relationship_type: str = Field(min_length=1, max_length=64)
    company_ids: list[UUID] = Field(min_length=1, max_length=100)
    role_id: UUID
    reason: str = Field(min_length=1, max_length=500)

    @field_validator('company_ids')
    @classmethod
    def reject_duplicate_companies(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError('empresas duplicadas não são permitidas')
        return value


class OnboardingResponse(BaseModel):
    user_id: UUID
    membership_id: UUID


class OffboardingRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class OffboardingResponse(BaseModel):
    status: str
    user_deactivated: bool


SessionDependency = Annotated[Session, Depends(get_db_session)]
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_authenticated_principal)]


@router.get('/context', response_model=IdentityContextResponse)
def context(
    company_id: Annotated[UUID, Query()],
    principal: PrincipalDependency,
    session: SessionDependency,
) -> IdentityContextResponse:
    contexts = _contexts(session)
    try:
        authorized = contexts.require(
            principal, PermissionCode('company.read'), company_id=company_id,
        )
    except AccessDeniedError:
        _access_denied()
    assert authorized.company_id is not None
    return IdentityContextResponse(
        tenant_id=authorized.tenant_id,
        user_id=authorized.user_id,
        membership_id=authorized.membership_id,
        company_id=authorized.company_id,
        permission=authorized.permission.value,
    )


@router.post('/onboarding', response_model=OnboardingResponse, status_code=201)
def onboard(
    payload: OnboardingRequest,
    request: Request,
    principal: PrincipalDependency,
    session: SessionDependency,
) -> OnboardingResponse:
    settings: AppSettings = request.app.state.settings
    if settings.oidc_issuer is None:
        raise HTTPException(status_code=503, detail='identity unavailable')
    service = _lifecycle(session, settings.oidc_issuer)
    correlation_id = UUID(request.state.correlation_id)
    try:
        with audit_scope(session, AuditContext(
            correlation_id=correlation_id,
            origin=AuditOrigin.API,
            actor_id=principal.user_id,
            reason=payload.reason,
        )):
            result = service.onboard(principal, OnboardIdentity(
                issuer=settings.oidc_issuer,
                subject=payload.provider_subject,
                display_name=payload.display_name,
                email=payload.email,
                relationship_type=payload.relationship_type,
                company_ids=tuple(payload.company_ids),
                role_id=payload.role_id,
                reason=payload.reason,
                correlation_id=correlation_id,
            ))
            session.flush()
    except (AccessDeniedError, IdentityLifecycleDeniedError):
        _access_denied()
    except IdentityLifecycleConflictError:
        raise HTTPException(status_code=409, detail='identity conflict') from None
    return OnboardingResponse(user_id=result.user_id, membership_id=result.membership_id)


@router.post('/users/{user_id}/offboard', response_model=OffboardingResponse)
def offboard(
    user_id: UUID,
    payload: OffboardingRequest,
    request: Request,
    principal: PrincipalDependency,
    session: SessionDependency,
) -> OffboardingResponse:
    settings: AppSettings = request.app.state.settings
    if settings.oidc_issuer is None:
        raise HTTPException(status_code=503, detail='identity unavailable')
    correlation_id = UUID(request.state.correlation_id)
    try:
        with audit_scope(session, AuditContext(
            correlation_id=correlation_id,
            origin=AuditOrigin.API,
            actor_id=principal.user_id,
            reason=payload.reason,
        )):
            changes = _lifecycle(session, settings.oidc_issuer).offboard(
                principal, user_id, reason=payload.reason,
                correlation_id=correlation_id,
            )
            session.flush()
    except (AccessDeniedError, IdentityLifecycleDeniedError):
        _access_denied()
    return OffboardingResponse(status='revoked', user_deactivated=changes.user_deactivated)


def _contexts(session: Session) -> IdentityContextService:
    return IdentityContextService(
        SqlAlchemyIdentityDirectory(session),
        AuthorizationService(SqlAlchemyAuthorizationRepository(session)),
    )


def _lifecycle(session: Session, issuer: str) -> IdentityLifecycleService:
    return IdentityLifecycleService(
        SqlAlchemyIdentityLifecycleRepository(session),
        _contexts(session),
        AuditService(SqlAlchemyAuditRepository(session)),
        allowed_issuer=issuer,
    )


def _access_denied() -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='access denied')
