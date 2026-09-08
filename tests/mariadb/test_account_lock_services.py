'''Provas operacionais de AccountLock contra o MariaDB descartável autorizado.'''

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from dotenv import dotenv_values
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import create_database_engine, create_session_factory
from serdial21.bootstrap.locks import create_account_lock_runtime
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel, CompanyModel, PermissionModel, RoleBindingModel, RoleModel,
    RolePermissionModel, TenantMembershipModel, TenantModel, UserModel,
)
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.locks.adapters.outbound.persistence.models import AccountLockModel
from serdial21.modules.locks.adapters.outbound.persistence.repositories import SQLAlchemyAccountLockRepository
from serdial21.modules.locks.application.services.persistent_locks import (
    AccountLockConflictError, CreateAccountLockCommand, ReleaseAccountLockCommand,
)
from serdial21.modules.locks.domain.entities import EffectChannel, EffectContext, EffectOperation, LockScope


NOW = datetime(2026, 9, 7, 15, 0, tzinfo=UTC)
_config = dotenv_values('.env.mysql-homologation')
pytestmark = [pytest.mark.mariadb_runtime, pytest.mark.skipif(
    _config.get('SERDIAL21_RUN_MARIADB_HOMOLOGATION') != '1',
    reason='homologação MariaDB exige opt-in explícito',
)]


def _url() -> str:
    url = _config.get('DATABASE_URL')
    assert url
    return url


def _seed(session: object) -> tuple[UUID, UUID, UUID, UUID, UUID]:
    tenant_id, company_id, company_b_id, allowed_user, denied_user = (uuid4() for _ in range(5))
    membership_id, role_id = (uuid4() for _ in range(2))
    permission = session.scalar(select(PermissionModel).where(PermissionModel.code == 'lock.manage'))  # type: ignore[attr-defined]
    assert permission is not None
    with audit_scope(session, AuditContext(uuid4(), actor_id=allowed_user, origin=AuditOrigin.AUTOMATION, reason='MariaDB AccountLock test fixture')):  # type: ignore[arg-type]
        session.add_all([  # type: ignore[attr-defined]
            TenantModel(id=tenant_id, name=f'Lock tenant {tenant_id}', timezone='UTC', currency_code='BRL', status='active'),
            UserModel(id=allowed_user, provider_subject=f'lock-allowed-{allowed_user}', display_name='Lock Allowed', is_active=True),
            UserModel(id=denied_user, provider_subject=f'lock-denied-{denied_user}', display_name='Lock Denied', is_active=True),
        ])
        session.flush()  # type: ignore[attr-defined]
        session.add_all([  # type: ignore[attr-defined]
            CompanyModel(id=company_id, tenant_id=tenant_id, legal_name='Lock Company', tax_identifier=str(uuid4().int)[:14], timezone='UTC', currency_code='BRL', status='active', valid_from=NOW - timedelta(days=1)),
            CompanyModel(id=company_b_id, tenant_id=tenant_id, legal_name='Lock Company B', tax_identifier=str(uuid4().int)[:14], timezone='UTC', currency_code='BRL', status='active', valid_from=NOW - timedelta(days=1)),
            TenantMembershipModel(id=membership_id, tenant_id=tenant_id, user_id=allowed_user, status='active', relationship_type='employee', valid_from=NOW - timedelta(days=1), revision=1),
            RoleModel(id=role_id, tenant_id=tenant_id, name=f'lock-manager-{role_id}', is_active=True),
        ])
        session.flush()  # type: ignore[attr-defined]
        session.add_all([  # type: ignore[attr-defined]
            CompanyAccessModel(tenant_id=tenant_id, membership_id=membership_id, company_id=company_id, status='active', valid_from=NOW - timedelta(days=1)),
            RolePermissionModel(tenant_id=tenant_id, role_id=role_id, permission_id=permission.id),
            RoleBindingModel(tenant_id=tenant_id, membership_id=membership_id, role_id=role_id, company_id=company_id, status='active', valid_from=NOW - timedelta(days=1)),
        ])
        session.commit()  # type: ignore[attr-defined]
    return tenant_id, company_id, company_b_id, allowed_user, denied_user


def _command(tenant_id: UUID, company_id: UUID, actor_id: UUID, account_id: UUID) -> CreateAccountLockCommand:
    return CreateAccountLockCommand(tenant_id, company_id, actor_id, LockScope.ACCOUNT, (EffectOperation.ALTER,), 'MariaDB controlled lock', uuid4(), account_id=account_id)


@pytest.fixture
def factory() -> object:
    engine = create_database_engine(AppSettings(database_url=_url()))
    load_models()
    try:
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT DATABASE()')) == 'u621451815_serdial21_hom'
        yield create_session_factory(engine)
    finally:
        engine.dispose()


def test_account_lock_application_persistence_release_rollback_and_isolation(factory: object) -> None:
    session = factory()  # type: ignore[operator]
    try:
        tenant_id, company_id, company_b_id, allowed_user, denied_user = _seed(session)
        runtime = create_account_lock_runtime(session, clock=lambda: NOW)
        account_id = uuid4()
        lock = runtime.create.execute(_command(tenant_id, company_id, allowed_user, account_id))
        session.commit()

        fresh = factory()  # type: ignore[operator]
        try:
            fresh_runtime = create_account_lock_runtime(fresh, clock=lambda: NOW)
            assert SQLAlchemyAccountLockRepository(fresh).get(tenant_id, lock.id) is not None
            with pytest.raises(Exception) as blocked:
                fresh_runtime.guard.validate(EffectContext(tenant_id, company_id, account_id, (), 'accounting', NOW.date(), EffectOperation.ALTER, EffectChannel.API))
            assert getattr(blocked.value, 'code', None) == 'account_locked'
            with pytest.raises(PermissionError):
                fresh_runtime.release.execute(ReleaseAccountLockCommand(tenant_id, company_id, denied_user, lock.id, 'not allowed', uuid4()))
            with pytest.raises(PermissionError):
                fresh_runtime.release.execute(ReleaseAccountLockCommand(tenant_id, company_b_id, allowed_user, lock.id, 'wrong company', uuid4()))
            assert SQLAlchemyAccountLockRepository(fresh).get(tenant_id, lock.id).status.value == 'ACTIVE'  # type: ignore[union-attr]
            assert fresh.scalar(select(func.count()).select_from(AuditEventModel).where(AuditEventModel.subject_id == lock.id)) == 1
        finally:
            fresh.close()

        runtime.release.execute(ReleaseAccountLockCommand(tenant_id, company_id, allowed_user, lock.id, 'released correctly', uuid4()))
        session.rollback()
        verify = factory()  # type: ignore[operator]
        try:
            assert SQLAlchemyAccountLockRepository(verify).get(tenant_id, lock.id).status.value == 'ACTIVE'  # type: ignore[union-attr]
            assert verify.scalar(select(func.count()).select_from(AuditEventModel).where(AuditEventModel.subject_id == lock.id)) == 1
        finally:
            verify.close()

        runtime.release.execute(ReleaseAccountLockCommand(tenant_id, company_id, allowed_user, lock.id, 'released correctly', uuid4()))
        session.commit()
        assert session.get(AccountLockModel, lock.id).active_marker is None  # type: ignore[union-attr]
        assert session.scalar(select(func.count()).select_from(AuditEventModel).where(AuditEventModel.subject_id == lock.id)) == 2

        transient = runtime.create.execute(_command(tenant_id, company_id, allowed_user, uuid4()))
        session.rollback()
        assert SQLAlchemyAccountLockRepository(session).get(tenant_id, transient.id) is None
        assert session.scalar(select(func.count()).select_from(AuditEventModel).where(AuditEventModel.subject_id == transient.id)) == 0
        assert SQLAlchemyAccountLockRepository(session).get(uuid4(), lock.id) is None
    finally:
        session.close()


def test_two_independent_sessions_create_only_one_active_equivalent_lock(factory: object) -> None:
    seed_session = factory()  # type: ignore[operator]
    try:
        tenant_id, company_id, _, actor_id, _ = _seed(seed_session)
    finally:
        seed_session.close()
    account_id = uuid4()

    def attempt() -> str:
        session = factory()  # type: ignore[operator]
        try:
            create_account_lock_runtime(session, clock=lambda: NOW).create.execute(_command(tenant_id, company_id, actor_id, account_id))
            session.commit()
            return 'created'
        except AccountLockConflictError:
            session.rollback()
            return 'conflict'
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: attempt(), range(2)))
    assert sorted(outcomes) == ['conflict', 'created']
    verify = factory()  # type: ignore[operator]
    try:
        assert verify.scalar(select(func.count()).select_from(AccountLockModel).where(AccountLockModel.tenant_id == tenant_id, AccountLockModel.company_id == company_id, AccountLockModel.active_marker == 'ACTIVE')) == 1
    finally:
        verify.close()
