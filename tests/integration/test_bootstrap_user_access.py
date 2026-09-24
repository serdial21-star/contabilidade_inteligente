'''Provisionamento do usuário da ponte de login (ADR 0014): idempotente e isolado por tenant.'''

from collections.abc import Generator
from datetime import UTC, datetime
import importlib.util
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel,
    CompanyModel,
    PermissionModel,
    RoleBindingModel,
    RolePermissionModel,
    TenantModel,
)
from serdial21.modules.audit.domain.entities import AuditOrigin


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def _load_script():
    spec = importlib.util.spec_from_file_location(
        'bootstrap_user_access', ROOT / 'scripts' / 'bootstrap_user_access.py',
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT = _load_script()


@pytest.fixture
def session() -> Generator[Session, None, None]:
    settings = AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:')
    engine = create_database_engine(settings)
    load_models()
    Base.metadata.create_all(engine)
    db = create_session_factory(engine)()
    db.add(PermissionModel(
        id=uuid4(), code='company.read', description='company.read', version=1, is_active=True,
    ))
    db.commit()
    try:
        yield db
    finally:
        db.close()


def _ctx() -> AuditContext:
    return AuditContext(correlation_id=uuid4(), origin=AuditOrigin.HUMAN, reason='teste')


def _tenant(db: Session, name: str = 'Serdial21') -> TenantModel:
    tenant = TenantModel(
        id=uuid4(), name=name, timezone='America/Sao_Paulo', currency_code='BRL', status='active',
    )
    db.add(tenant)
    with audit_scope(db, _ctx()):
        db.commit()
    return tenant


def _company(db: Session, tenant: TenantModel, tax_identifier: str) -> CompanyModel:
    company = CompanyModel(
        id=uuid4(), tenant_id=tenant.id, legal_name='Empresa Teste', tax_identifier=tax_identifier,
        timezone='America/Sao_Paulo', currency_code='BRL', status='active', valid_from=NOW,
    )
    db.add(company)
    with audit_scope(db, _ctx()):
        db.commit()
    return company


def _provision(db: Session, tenant: TenantModel, **overrides: object) -> dict:
    base = dict(
        issuer='https://sistemaa.serdial21.com', subject='funcionario:1',
        display_name='Sergio', email=None,
    )
    base.update(overrides)
    permissions = ('company.read',)
    with audit_scope(db, _ctx()):
        user = SCRIPT._find_or_create_user(db, issuer=base['issuer'], subject=base['subject'],
                                            display_name=base['display_name'], email=base['email'])
        membership = SCRIPT._find_or_create_membership(db, tenant_id=tenant.id, user_id=user.id, now=NOW)
        role = SCRIPT._find_or_create_role(db, tenant_id=tenant.id, name=SCRIPT.DEFAULT_ROLE_NAME)
        SCRIPT._ensure_role_permissions(db, tenant_id=tenant.id, role_id=role.id, codes=permissions)
        SCRIPT._ensure_tenant_wide_role_binding(
            db, tenant_id=tenant.id, membership_id=membership.id, role_id=role.id, now=NOW)
        for company_id in db.scalars(select(CompanyModel.id).where(CompanyModel.tenant_id == tenant.id)):
            SCRIPT._ensure_company_access(
                db, tenant_id=tenant.id, membership_id=membership.id, company_id=company_id, now=NOW)
        db.commit()
    return {'user_id': user.id, 'membership_id': membership.id, 'role_id': role.id}


def test_provisioning_grants_access_to_every_company(session: Session) -> None:
    tenant = _tenant(session)
    _company(session, tenant, '11111111000111')
    _company(session, tenant, '22222222000122')
    result = _provision(session, tenant)
    accesses = session.scalars(select(CompanyAccessModel).where(
        CompanyAccessModel.membership_id == result['membership_id'])).all()
    assert len(accesses) == 2


def test_provisioning_is_idempotent(session: Session) -> None:
    tenant = _tenant(session)
    _company(session, tenant, '11111111000111')
    first = _provision(session, tenant)
    second = _provision(session, tenant)
    assert first == second
    assert len(session.scalars(select(RoleBindingModel)).all()) == 1
    assert len(session.scalars(select(RolePermissionModel)).all()) == 1
    assert len(session.scalars(select(CompanyAccessModel)).all()) == 1


def test_same_issuer_and_subject_in_two_tenants_are_isolated(session: Session) -> None:
    tenant_a = _tenant(session, 'A')
    tenant_b = _tenant(session, 'B')
    _company(session, tenant_a, '11111111000111')
    _company(session, tenant_b, '22222222000122')
    result_a = _provision(session, tenant_a)
    result_b = _provision(session, tenant_b)
    assert result_a['user_id'] == result_b['user_id']  # mesma identidade (iss+sub)…
    assert result_a['membership_id'] != result_b['membership_id']  # …mas vínculo por tenant é distinto
    accesses_a = session.scalars(select(CompanyAccessModel).where(
        CompanyAccessModel.tenant_id == tenant_a.id)).all()
    accesses_b = session.scalars(select(CompanyAccessModel).where(
        CompanyAccessModel.tenant_id == tenant_b.id)).all()
    assert len(accesses_a) == 1 and len(accesses_b) == 1
    assert accesses_a[0].company_id != accesses_b[0].company_id
