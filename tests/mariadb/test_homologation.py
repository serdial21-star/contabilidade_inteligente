"""Homologação destrutiva, opt-in, para o banco MariaDB dedicado.

Nunca é coletada por acidente: exige o sinal explícito de ambiente e recusa
qualquer database que não seja o banco descartável aprovado.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from serdial21.bootstrap.database import UTCDateTime, create_database_engine, normalized_database_url
from serdial21.bootstrap.settings import AppSettings, get_settings
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel


EXPECTED_DATABASE = 'u621451815_serdial21_mig'
REVISIONS = (
    '20260903_0001', '20260903_0002', '20260904_0003', '20260904_0004',
    '20260904_0005', '20260905_0006', '20260906_0007', '20260906_0008',
    '20260907_0009', '20260908_0010', '20260908_0011',
)
pytestmark = pytest.mark.mariadb_migration


def _require_opt_in() -> None:
    if os.environ.get('SERDIAL21_RUN_MARIADB_MIGRATION_TESTS') != '1':
        pytest.skip('homologação MariaDB exige SERDIAL21_RUN_MARIADB_MIGRATION_TESTS=1')


def _homologation_settings() -> AppSettings:
    values = dotenv_values('.env.mariadb-migration-lab')
    database_url = values.get('MARIADB_MIGRATION_DATABASE_URL')
    assert database_url, 'DATABASE_URL ausente no arquivo de homologação'
    return AppSettings(database_url=database_url)


@pytest.fixture
def mariadb_engine(migration_lab_at_revision: object) -> Engine:
    _require_opt_in()
    with migration_lab_at_revision('base') as engine:  # type: ignore[operator]
        with engine.connect() as connection:
            version, database = connection.execute(text('SELECT VERSION(), DATABASE()')).one()
            assert 'MariaDB' in version and version.startswith('11.8.'), version
            assert database == EXPECTED_DATABASE, database
            assert set(inspect(connection).get_table_names()) <= {'alembic_version'}
        yield engine


def test_00_preflight_read_only(mariadb_engine: Engine) -> None:
    with mariadb_engine.connect() as connection:
        version, database, current_user, timezone, charset, collation = connection.execute(text(
            'SELECT VERSION(), DATABASE(), CURRENT_USER(), @@session.time_zone, '
            '@@character_set_connection, @@collation_connection'
        )).one()
    print(f'VERSION={version}')
    print(f'DATABASE={database}')
    print(f'CURRENT_USER={current_user}')
    print(f'TIME_ZONE={timezone}')
    print(f'CHARSET={charset}')
    print(f'COLLATION={collation}')
    assert database == EXPECTED_DATABASE
    assert 'MariaDB' in version and version.startswith('11.8.')
    assert timezone == '+00:00'
    assert charset == 'utf8mb4'


@pytest.fixture
def migrated_engine(mariadb_engine: Engine) -> Engine:
    config = Config('alembic.ini')
    settings = _homologation_settings()
    assert settings.database_url is not None
    os.environ['DATABASE_URL'] = settings.database_url.get_secret_value()
    get_settings.cache_clear()
    config.set_main_option('sqlalchemy.url', str(normalized_database_url(settings)))
    for revision in REVISIONS:
        command.upgrade(config, revision)
    command.upgrade(config, 'head')
    with mariadb_engine.connect() as connection:
        assert connection.scalar(text('SELECT DATABASE()')) == EXPECTED_DATABASE
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == REVISIONS[-1]
    return mariadb_engine


def _tenant_values(identifier: str, name: str = 'Contabilidade 📊') -> dict[str, object]:
    return {
        'id': identifier,
        'name': name,
        'timezone': 'UTC',
        'currency_code': 'BRL',
        'status': 'ACTIVE',
    }


def test_schema_and_connection_settings(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        assert {'tenants', 'companies', 'company_accesses', 'audit_events',
                'import_batches', 'fiscal_documents', 'bank_transactions',
                'nfe_journey_checkpoints'} <= tables
        engines = connection.execute(text(
            "SELECT DISTINCT ENGINE FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN "
            "('tenants','companies','company_accesses','audit_events','import_batches',"
            "'fiscal_documents','bank_transactions','nfe_journey_checkpoints')"
        )).scalars().all()
        assert engines and set(engines) == {'InnoDB'}
        assert connection.scalar(text('SELECT @@session.time_zone')) == '+00:00'
        assert connection.scalar(text('SELECT @@character_set_connection')) == 'utf8mb4'
        assert connection.scalar(text("SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS "
                                      "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='audit_events' "
                                      "AND CONSTRAINT_TYPE='CHECK'")) >= 1
        assert len(inspector.get_foreign_keys('company_accesses')) >= 2
        assert any(item['name'] == 'uq_import_batches_scope_idempotency'
                   for item in inspector.get_unique_constraints('import_batches'))


def test_utf8_utc_boolean_decimal_json_and_audit_check(migrated_engine: Engine) -> None:
    tenant_id = uuid4().hex
    with migrated_engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(
                'INSERT INTO tenants (id,name,timezone,currency_code,status) '
                'VALUES (:id,:name,:timezone,:currency_code,:status)'
            ), _tenant_values(tenant_id))
            assert connection.scalar(text('SELECT name FROM tenants WHERE id=:id'), {'id': tenant_id}) == 'Contabilidade 📊'
            values = connection.execute(text(
                'SELECT CAST(123456789012345678.12 AS DECIMAL(20,2)), '
                'CAST(1.123456 AS DECIMAL(20,6)), '
                'CAST(1.1234567890 AS DECIMAL(20,10)), '
                'CAST(1.123456 AS DECIMAL(12,6))'
            )).one()
            assert tuple(str(value) for value in values) == ('123456789012345678.12', '1.123456', '1.1234567890', '1.123456')
            session = Session(connection)
            event = AuditEventModel(
                id=uuid4(), tenant_id=uuid4(), company_id=None, actor_id=None,
                origin='IMPORT', module='homologation', action='round_trip',
                subject_type='probe', subject_id=uuid4(), subject_version=None,
                before_state={'nested': {'value': 1}, 'items': [1, 2]}, after_state=None,
                reason=None, correlation_id=uuid4(), causation_id=None,
                occurred_at=datetime.now(UTC), integrity_hash='0' * 64,
            )
            event.tenant_id = __import__('uuid').UUID(hex=tenant_id)
            session.add(event)
            session.flush()
            assert session.get(AuditEventModel, event.id).before_state == {'nested': {'value': 1}, 'items': [1, 2]}
            session.rollback()
            with pytest.raises(DBAPIError):
                connection.execute(text(
                    "INSERT INTO audit_events (id,tenant_id,origin,module,action,subject_type,subject_id,correlation_id,occurred_at,integrity_hash) "
                    "VALUES (:id,:tenant_id,'INVALID','x','x','x',:subject_id,:correlation_id,UTC_TIMESTAMP(),:integrity_hash)"
                ), {'id': uuid4().hex, 'tenant_id': tenant_id, 'subject_id': uuid4().hex,
                    'correlation_id': uuid4().hex, 'integrity_hash': '0' * 64})
        finally:
            if transaction.is_active:
                transaction.rollback()


def test_utc_type_round_trip(migrated_engine: Engine) -> None:
    bind = UTCDateTime()
    now = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    with migrated_engine.connect() as connection:
        assert bind.process_result_value(bind.process_bind_param(now, connection.dialect), connection.dialect) == now
