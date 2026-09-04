from collections.abc import Generator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import (
    AuditContext,
    MissingAuditContextError,
    audit_scope,
)
from serdial21.bootstrap.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyModel,
    RoleBindingModel,
    RoleModel,
    TenantMembershipModel,
    TenantModel,
    UserModel,
)
from serdial21.modules.audit.adapters.outbound.persistence.models import (
    AuditEventModel,
)
from serdial21.modules.audit.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import (
    AuditEventImmutableError,
    AuditOrigin,
)


NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


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
    session = create_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def tenant(tenant_id: UUID, name: str) -> TenantModel:
    return TenantModel(
        id=tenant_id,
        name=name,
        timezone='America/Sao_Paulo',
        currency_code='BRL',
        status='active',
    )


def context(correlation_id: UUID) -> AuditContext:
    return AuditContext(
        correlation_id=correlation_id,
        origin=AuditOrigin.API,
        actor_id=uuid4(),
        reason='approved test change',
    )


def test_commit_hook_creates_correlated_event(
    database_session: Session,
) -> None:
    tenant_id = uuid4()
    correlation_id = uuid4()
    with audit_scope(database_session, context(correlation_id)):
        database_session.add(tenant(tenant_id, 'Tenant A'))
        database_session.commit()

    service = AuditService(SqlAlchemyAuditRepository(database_session))
    events = service.list_by_correlation(tenant_id, correlation_id)

    assert len(events) == 1
    assert events[0].action == 'tenant.created'
    assert events[0].before is None
    assert events[0].after == {
        'status': 'active',
        'timezone': 'America/Sao_Paulo',
        'currency_code': 'BRL',
    }
    assert service.verify_integrity(events[0]) is True


def test_repository_never_returns_event_from_another_tenant(
    database_session: Session,
) -> None:
    tenant_a_id = uuid4()
    tenant_b_id = uuid4()
    correlation_id = uuid4()
    with audit_scope(database_session, context(correlation_id)):
        database_session.add_all([
            tenant(tenant_a_id, 'Tenant A'),
            tenant(tenant_b_id, 'Tenant B'),
        ])
        database_session.commit()

    service = AuditService(SqlAlchemyAuditRepository(database_session))
    event_b = service.list_by_correlation(tenant_b_id, correlation_id)[0]

    assert service.get(tenant_a_id, event_b.id) is None
    assert [
        item.tenant_id
        for item in service.list_by_correlation(tenant_a_id, correlation_id)
    ] == [tenant_a_id]


def test_company_reference_cannot_cross_tenants(
    database_session: Session,
) -> None:
    tenant_a_id = uuid4()
    tenant_b_id = uuid4()
    company_b_id = uuid4()
    with audit_scope(database_session, context(uuid4())):
        database_session.add_all([
            tenant(tenant_a_id, 'Tenant A'),
            tenant(tenant_b_id, 'Tenant B'),
        ])
        database_session.flush()
        database_session.add(
            CompanyModel(
                id=company_b_id,
                tenant_id=tenant_b_id,
                legal_name='Company B',
                tax_identifier='00000000000002',
                timezone='America/Sao_Paulo',
                currency_code='BRL',
                status='active',
                valid_from=NOW,
            )
        )
        database_session.commit()

    AuditService(SqlAlchemyAuditRepository(database_session)).record(
        AuditRecord(
            tenant_id=tenant_a_id,
            company_id=company_b_id,
            actor_id=None,
            origin=AuditOrigin.AUTOMATION,
            module='test',
            action='invalid.reference',
            subject_type='Company',
            subject_id=company_b_id,
            subject_version=None,
            before=None,
            after={'status': 'active'},
            reason='cross-tenant test',
            correlation_id=uuid4(),
        )
    )
    with pytest.raises(IntegrityError):
        database_session.commit()
    database_session.rollback()


def test_persisted_event_cannot_be_updated(
    database_session: Session,
) -> None:
    tenant_id = uuid4()
    with audit_scope(database_session, context(uuid4())):
        database_session.add(tenant(tenant_id, 'Tenant A'))
        database_session.commit()

    audit_event = database_session.scalar(select(AuditEventModel))
    assert audit_event is not None
    audit_event.action = 'tenant.deleted'

    with pytest.raises(AuditEventImmutableError):
        database_session.commit()
    database_session.rollback()


def test_critical_change_without_audit_context_fails_closed(
    database_session: Session,
) -> None:
    database_session.add(tenant(uuid4(), 'Tenant without context'))

    with pytest.raises(MissingAuditContextError):
        database_session.commit()
    database_session.rollback()


def test_business_change_and_audit_event_rollback_together(
    database_session: Session,
) -> None:
    tenant_id = uuid4()
    with audit_scope(database_session, context(uuid4())):
        database_session.add(tenant(tenant_id, 'Rolled back tenant'))
        database_session.flush()
        database_session.rollback()

    tenant_count = database_session.scalar(
        select(func.count()).select_from(TenantModel)
    )
    audit_count = database_session.scalar(
        select(func.count()).select_from(AuditEventModel)
    )
    assert tenant_count == 0
    assert audit_count == 0


def test_commit_hook_audits_creation_and_change_of_initial_entities(
    database_session: Session,
) -> None:
    ids = [uuid4() for _ in range(6)]
    tenant_id, user_id, membership_id, company_id, role_id, binding_id = ids
    creation_correlation = uuid4()
    tenant_model = tenant(tenant_id, 'Tenant A')
    user_model = UserModel(
        id=user_id,
        provider_subject='audit-user',
        display_name='Audit User',
        is_active=True,
    )
    with audit_scope(database_session, context(creation_correlation)):
        database_session.add_all([tenant_model, user_model])
        database_session.flush()
        membership_model = TenantMembershipModel(
            id=membership_id,
            tenant_id=tenant_id,
            user_id=user_id,
            status='active',
            relationship_type='employee',
            valid_from=NOW,
            revision=1,
        )
        company_model = CompanyModel(
            id=company_id,
            tenant_id=tenant_id,
            legal_name='Company A',
            tax_identifier='00000000000001',
            timezone='America/Sao_Paulo',
            currency_code='BRL',
            status='active',
            valid_from=NOW,
        )
        role_model = RoleModel(
            id=role_id,
            tenant_id=tenant_id,
            name='auditor',
            is_active=True,
        )
        database_session.add_all([membership_model, company_model, role_model])
        database_session.flush()
        binding_model = RoleBindingModel(
            id=binding_id,
            tenant_id=tenant_id,
            membership_id=membership_id,
            role_id=role_id,
            company_id=company_id,
            status='active',
            valid_from=NOW,
        )
        database_session.add(binding_model)
        database_session.commit()

    audit_service = AuditService(SqlAlchemyAuditRepository(database_session))
    created_actions = {
        item.action
        for item in audit_service.list_by_correlation(
            tenant_id,
            creation_correlation,
        )
    }
    assert created_actions == {
        'tenant.created',
        'company.created',
        'membership.created',
        'role_binding.created',
    }

    update_correlation = uuid4()
    with audit_scope(database_session, context(update_correlation)):
        tenant_model.status = 'suspended'
        company_model.status = 'suspended'
        membership_model.status = 'revoked'
        membership_model.revision = 2
        binding_model.status = 'revoked'
        database_session.commit()

    updated_events = audit_service.list_by_correlation(
        tenant_id,
        update_correlation,
    )
    assert {item.action for item in updated_events} == {
        'tenant.updated',
        'company.updated',
        'membership.updated',
        'role_binding.updated',
    }
    membership_event = next(
        item for item in updated_events if item.action == 'membership.updated'
    )
    assert membership_event.before == {'status': 'active', 'revision': 1}
    assert membership_event.after == {'status': 'revoked', 'revision': 2}
    assert membership_event.subject_version == 2
