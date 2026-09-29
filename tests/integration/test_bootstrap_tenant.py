'''Bootstrap de tenant com identificador explícito e conflitos fail-closed.'''

from collections.abc import Generator
import importlib.util
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import TenantModel
from serdial21.modules.audit.domain.entities import AuditOrigin


ROOT = Path(__file__).resolve().parents[2]
APPROVED_TENANT_ID = UUID('5463ce7c-31b5-471d-97aa-89f043292ebb')


def _load_script():
    spec = importlib.util.spec_from_file_location(
        'bootstrap_tenant', ROOT / 'scripts' / 'bootstrap_tenant.py',
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT = _load_script()


@pytest.fixture
def session() -> Generator[Session, None, None]:
    settings = AppSettings(
        _env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:',
    )
    engine = create_database_engine(settings)
    load_models()
    Base.metadata.create_all(engine)
    db = create_session_factory(engine)()
    try:
        yield db
    finally:
        db.close()


def _prepare(
    session: Session, *, name: str = 'Serdial21', tenant_id: UUID | None = APPROVED_TENANT_ID,
) -> tuple[TenantModel, bool]:
    return SCRIPT._find_or_prepare_tenant(
        session,
        name=name,
        tenant_id=tenant_id,
        timezone='America/Sao_Paulo',
        currency='BRL',
    )


def _commit(session: Session) -> None:
    context = AuditContext(
        correlation_id=uuid4(), origin=AuditOrigin.HUMAN,
        reason='teste do bootstrap de tenant',
    )
    with audit_scope(session, context):
        session.commit()


def test_prepares_tenant_with_explicit_approved_identifier(session: Session) -> None:
    tenant, created = _prepare(session)
    assert created is True
    assert tenant.id == APPROVED_TENANT_ID


def test_same_name_and_identifier_are_idempotent(session: Session) -> None:
    tenant, _ = _prepare(session)
    _commit(session)
    existing, created = _prepare(session)
    assert created is False
    assert existing.id == tenant.id


def test_same_name_with_different_identifier_is_rejected(session: Session) -> None:
    _prepare(session)
    _commit(session)
    with pytest.raises(SystemExit, match='identificador diferente'):
        _prepare(session, tenant_id=uuid4())


def test_same_identifier_with_different_name_is_rejected(session: Session) -> None:
    _prepare(session)
    _commit(session)
    with pytest.raises(SystemExit, match='já pertence a outro nome'):
        _prepare(session, name='Outro Escritório')
