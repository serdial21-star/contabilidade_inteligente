from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from serdial21.bootstrap.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel,
    CompanyModel,
    EstablishmentModel,
    PermissionModel,
    RoleBindingModel,
    RoleModel,
    RolePermissionModel,
    TenantMembershipModel,
    TenantModel,
    UserModel,
)
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuthorizationRepository,
)
from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError,
    AuthorizationRequest,
    AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.domain.entities import AuditOrigin


NOW = datetime(2026, 9, 3, 15, 0, tzinfo=UTC)


@dataclass(frozen=True)
class BoundaryIds:
    tenant_a: UUID
    tenant_b: UUID
    user_a: UUID
    user_b: UUID
    membership_a: UUID
    membership_b: UUID
    company_a: UUID
    company_b: UUID
    role_a: UUID
    role_b: UUID
    permission_read: UUID


@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    settings = AppSettings(
        _env_file=None,
        environment='test',
        database_url='sqlite+pysqlite:///:memory:',
    )
    engine = create_database_engine(settings)
    load_models()
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    session = factory()
    try:
        with audit_scope(
            session,
            AuditContext(
                correlation_id=uuid4(),
                origin=AuditOrigin.AUTOMATION,
                reason='security test fixture',
            ),
        ):
            yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def boundary(database_session: Session) -> BoundaryIds:
    ids = BoundaryIds(*(uuid4() for _ in range(11)))
    database_session.add_all(
        [
            TenantModel(
                id=ids.tenant_a,
                name='Tenant A',
                timezone='America/Sao_Paulo',
                currency_code='BRL',
                status='active',
            ),
            TenantModel(
                id=ids.tenant_b,
                name='Tenant B',
                timezone='America/Sao_Paulo',
                currency_code='BRL',
                status='active',
            ),
            UserModel(
                id=ids.user_a,
                provider_subject='provider-user-a',
                display_name='User A',
                is_active=True,
            ),
            UserModel(
                id=ids.user_b,
                provider_subject='provider-user-b',
                display_name='User B',
                is_active=True,
            ),
            PermissionModel(
                id=ids.permission_read,
                code='company.read',
                description='company.read',
                version=1,
                is_active=True,
            ),
        ]
    )
    database_session.flush()
    database_session.add_all(
        [
            TenantMembershipModel(
                id=ids.membership_a,
                tenant_id=ids.tenant_a,
                user_id=ids.user_a,
                status='active',
                relationship_type='employee',
                valid_from=NOW - timedelta(days=1),
                revision=1,
            ),
            TenantMembershipModel(
                id=ids.membership_b,
                tenant_id=ids.tenant_b,
                user_id=ids.user_b,
                status='active',
                relationship_type='employee',
                valid_from=NOW - timedelta(days=1),
                revision=1,
            ),
            CompanyModel(
                id=ids.company_a,
                tenant_id=ids.tenant_a,
                legal_name='Company A',
                tax_identifier='00000000000001',
                timezone='America/Sao_Paulo',
                currency_code='BRL',
                status='active',
                valid_from=NOW - timedelta(days=1),
            ),
            CompanyModel(
                id=ids.company_b,
                tenant_id=ids.tenant_b,
                legal_name='Company B',
                tax_identifier='00000000000002',
                timezone='America/Sao_Paulo',
                currency_code='BRL',
                status='active',
                valid_from=NOW - timedelta(days=1),
            ),
            RoleModel(
                id=ids.role_a,
                tenant_id=ids.tenant_a,
                name='reader-a',
                is_active=True,
            ),
            RoleModel(
                id=ids.role_b,
                tenant_id=ids.tenant_b,
                name='reader-b',
                is_active=True,
            ),
        ]
    )
    database_session.flush()
    database_session.add_all(
        [
            CompanyAccessModel(
                tenant_id=ids.tenant_a,
                membership_id=ids.membership_a,
                company_id=ids.company_a,
                status='active',
                valid_from=NOW - timedelta(days=1),
            ),
            RolePermissionModel(
                tenant_id=ids.tenant_a,
                role_id=ids.role_a,
                permission_id=ids.permission_read,
            ),
            RoleBindingModel(
                tenant_id=ids.tenant_a,
                membership_id=ids.membership_a,
                role_id=ids.role_a,
                company_id=ids.company_a,
                status='active',
                valid_from=NOW - timedelta(days=1),
            ),
        ]
    )
    database_session.commit()
    return ids


def authorization_service(session: Session) -> AuthorizationService:
    return AuthorizationService(SqlAlchemyAuthorizationRepository(session))


def test_user_can_read_authorized_company(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    context = authorization_service(database_session).require(
        AuthorizationRequest(
            tenant_id=boundary.tenant_a,
            user_id=boundary.user_a,
            company_id=boundary.company_a,
            permission=PermissionCode('company.read'),
        ),
        at=NOW,
    )

    assert context.membership_id == boundary.membership_a
    assert context.tenant_id == boundary.tenant_a
    assert context.company_id == boundary.company_a


def test_known_ids_never_authorize_cross_tenant_access(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    service = authorization_service(database_session)
    attempts = (
        AuthorizationRequest(
            tenant_id=boundary.tenant_b,
            user_id=boundary.user_a,
            company_id=boundary.company_b,
            permission=PermissionCode('company.read'),
        ),
        AuthorizationRequest(
            tenant_id=boundary.tenant_a,
            user_id=boundary.user_a,
            company_id=boundary.company_b,
            permission=PermissionCode('company.read'),
        ),
    )

    messages = []
    for request in attempts:
        with pytest.raises(AccessDeniedError) as denied:
            service.require(request, at=NOW)
        messages.append((denied.value.code, str(denied.value)))

    assert messages == [
        ('access_denied', 'access denied'),
        ('access_denied', 'access denied'),
    ]


def test_user_without_active_membership_is_denied(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    membership = database_session.get(TenantMembershipModel, boundary.membership_a)
    assert membership is not None
    membership.status = 'revoked'
    database_session.commit()

    with pytest.raises(AccessDeniedError):
        authorization_service(database_session).require(
            AuthorizationRequest(
                tenant_id=boundary.tenant_a,
                user_id=boundary.user_a,
                company_id=boundary.company_a,
                permission=PermissionCode('company.read'),
            ),
            at=NOW,
        )


def test_user_without_company_access_is_denied(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    access = database_session.query(CompanyAccessModel).filter_by(
        tenant_id=boundary.tenant_a,
        membership_id=boundary.membership_a,
        company_id=boundary.company_a,
    ).one()
    access.status = 'revoked'
    database_session.commit()

    with pytest.raises(AccessDeniedError):
        authorization_service(database_session).require(
            AuthorizationRequest(
                tenant_id=boundary.tenant_a,
                user_id=boundary.user_a,
                company_id=boundary.company_a,
                permission=PermissionCode('company.read'),
            ),
            at=NOW,
        )


def test_role_without_requested_permission_is_denied(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    with pytest.raises(AccessDeniedError):
        authorization_service(database_session).require(
            AuthorizationRequest(
                tenant_id=boundary.tenant_a,
                user_id=boundary.user_a,
                company_id=boundary.company_a,
                permission=PermissionCode('journal.approve'),
            ),
            at=NOW,
        )


def test_company_access_constraint_rejects_cross_tenant_association(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    database_session.add(
        CompanyAccessModel(
            tenant_id=boundary.tenant_b,
            membership_id=boundary.membership_a,
            company_id=boundary.company_b,
            status='active',
            valid_from=NOW,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.commit()
    database_session.rollback()


def test_role_binding_constraint_rejects_cross_tenant_role(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    database_session.add(
        RoleBindingModel(
            tenant_id=boundary.tenant_b,
            membership_id=boundary.membership_b,
            role_id=boundary.role_a,
            company_id=boundary.company_b,
            status='active',
            valid_from=NOW,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.commit()
    database_session.rollback()


def test_role_permission_constraint_rejects_cross_tenant_role(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    database_session.add(
        RolePermissionModel(
            tenant_id=boundary.tenant_b,
            role_id=boundary.role_a,
            permission_id=boundary.permission_read,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.commit()
    database_session.rollback()


def test_establishment_constraint_rejects_cross_tenant_company(
    database_session: Session,
    boundary: BoundaryIds,
) -> None:
    database_session.add(
        EstablishmentModel(
            tenant_id=boundary.tenant_a,
            company_id=boundary.company_b,
            name='Invalid establishment',
            tax_identifier='00000000000003',
            status='active',
            valid_from=NOW,
        )
    )

    with pytest.raises(IntegrityError):
        database_session.commit()
    database_session.rollback()
