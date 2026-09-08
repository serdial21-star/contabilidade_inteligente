from collections.abc import Generator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import CompanyModel, TenantModel
from serdial21.modules.access_control.application.services.authorization import AuthorizedContext
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.locks.adapters.outbound.persistence.models import AccountLockModel
from serdial21.modules.locks.adapters.outbound.persistence.repositories import SQLAlchemyAccountLockRepository
from serdial21.modules.locks.application.services.locks import AccountLockService
from serdial21.modules.locks.application.services.persistent_locks import (
    CreateAccountLock, CreateAccountLockCommand, PersistedAccountLockGuard,
    ReleaseAccountLock, ReleaseAccountLockCommand, AccountLockConflictError,
)
from serdial21.modules.locks.domain.entities import (
    AccountLockedError, EffectChannel, EffectContext, EffectOperation, LockScope,
)


NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)


class Authorizer:
    def __init__(self, context: AuthorizedContext | None) -> None:
        self.context = context

    def require(self, *_: object, **__: object) -> AuthorizedContext:
        if self.context is None:
            raise PermissionError('access denied')
        return self.context


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_database_engine(AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:'))
    load_models()
    Base.metadata.create_all(engine)
    current = create_session_factory(engine)()
    try:
        yield current
    finally:
        current.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _seed(session: Session) -> tuple[UUID, UUID, UUID]:
    tenant_id, company_id, actor_id = uuid4(), uuid4(), uuid4()
    with audit_scope(session, AuditContext(uuid4(), origin=AuditOrigin.AUTOMATION, reason='lock fixture')):
        session.add(TenantModel(id=tenant_id, name='Tenant', timezone='UTC', currency_code='BRL', status='active'))
        session.flush()
        session.add(CompanyModel(id=company_id, tenant_id=tenant_id, legal_name='Company', tax_identifier='00000000000001', timezone='UTC', currency_code='BRL', status='active', valid_from=NOW))
        session.commit()
    return tenant_id, company_id, actor_id


def _runtime(session: Session, tenant_id: UUID, company_id: UUID, actor_id: UUID, *, allowed: bool = True) -> tuple[CreateAccountLock, ReleaseAccountLock, PersistedAccountLockGuard]:
    context = AuthorizedContext(tenant_id, actor_id, uuid4(), company_id, PermissionCode('lock.manage'), NOW) if allowed else None
    repository = SQLAlchemyAccountLockRepository(session)
    audit = AuditService(SqlAlchemyAuditRepository(session), clock=lambda: NOW)
    authorization = Authorizer(context)  # type: ignore[arg-type]
    return (
        CreateAccountLock(repository, authorization, audit, flush=session.flush, clock=lambda: NOW),  # type: ignore[arg-type]
        ReleaseAccountLock(repository, authorization, AccountLockService(audit), flush=session.flush, clock=lambda: NOW),  # type: ignore[arg-type]
        PersistedAccountLockGuard(repository),
    )


def _command(tenant_id: UUID, company_id: UUID, actor_id: UUID, account_id: UUID) -> CreateAccountLockCommand:
    return CreateAccountLockCommand(tenant_id, company_id, actor_id, LockScope.ACCOUNT, (EffectOperation.ALTER,), 'closed period', uuid4(), account_id=account_id)


def test_create_commit_guard_release_and_audit_share_one_session(session: Session) -> None:
    tenant_id, company_id, actor_id = _seed(session)
    account_id = uuid4()
    create, release, guard = _runtime(session, tenant_id, company_id, actor_id)
    lock = create.execute(_command(tenant_id, company_id, actor_id, account_id))
    session.commit()

    assert SQLAlchemyAccountLockRepository(session).get(tenant_id, lock.id) is not None
    with pytest.raises(AccountLockedError):
        guard.validate(EffectContext(tenant_id, company_id, account_id, (), 'accounting', NOW.date(), EffectOperation.ALTER, EffectChannel.API))
    assert session.scalar(select(func.count()).select_from(AuditEventModel).where(AuditEventModel.subject_id == lock.id)) == 1

    released = release.execute(ReleaseAccountLockCommand(tenant_id, company_id, actor_id, lock.id, 'correction', uuid4()))
    session.commit()
    assert released.status.value == 'RELEASED'
    assert session.get(AccountLockModel, lock.id).active_marker is None  # type: ignore[union-attr]
    assert session.scalar(select(func.count()).select_from(AuditEventModel).where(AuditEventModel.subject_id == lock.id)) == 2


def test_create_and_audit_rollback_together(session: Session) -> None:
    tenant_id, company_id, actor_id = _seed(session)
    create, _, _ = _runtime(session, tenant_id, company_id, actor_id)
    lock = create.execute(_command(tenant_id, company_id, actor_id, uuid4()))
    session.rollback()
    assert SQLAlchemyAccountLockRepository(session).get(tenant_id, lock.id) is None
    assert session.scalar(select(func.count()).select_from(AuditEventModel).where(AuditEventModel.subject_id == lock.id)) == 0


def test_release_denied_leaves_active_lock_and_no_release_audit(session: Session) -> None:
    tenant_id, company_id, actor_id = _seed(session)
    account_id = uuid4()
    create, _, _ = _runtime(session, tenant_id, company_id, actor_id)
    lock = create.execute(_command(tenant_id, company_id, actor_id, account_id))
    session.commit()
    _, denied_release, _ = _runtime(session, tenant_id, company_id, actor_id, allowed=False)
    with pytest.raises(PermissionError):
        denied_release.execute(ReleaseAccountLockCommand(tenant_id, company_id, actor_id, lock.id, 'no authority', uuid4()))
    assert SQLAlchemyAccountLockRepository(session).get(tenant_id, lock.id).status.value == 'ACTIVE'  # type: ignore[union-attr]
    assert session.scalar(select(func.count()).select_from(AuditEventModel).where(AuditEventModel.subject_id == lock.id)) == 1


def test_equivalent_active_locks_are_rejected_by_unique_constraint(session: Session) -> None:
    tenant_id, company_id, actor_id = _seed(session)
    account_id = uuid4()
    create, _, _ = _runtime(session, tenant_id, company_id, actor_id)
    create.execute(_command(tenant_id, company_id, actor_id, account_id))
    session.commit()
    with pytest.raises(AccountLockConflictError):
        create.execute(_command(tenant_id, company_id, actor_id, account_id))
    session.rollback()
