"""Read-only diagnosis for the partial schema left by migration 0006."""

from __future__ import annotations

import os

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
import pytest
from sqlalchemy import text

from serdial21.bootstrap.database import create_database_engine
from serdial21.bootstrap.settings import AppSettings, get_settings


EXPECTED_DATABASE = 'u621451815_serdial21_mig'
pytestmark = pytest.mark.mariadb_migration


@pytest.fixture
def at_0005(migration_lab_at_revision: object) -> object:
    with migration_lab_at_revision('20260904_0005') as engine:  # type: ignore[operator]
        yield engine


def test_migration_0006_parent_fk_diagnosis(at_0005: object) -> None:
    values = dotenv_values('.env.mariadb-migration-lab')
    database_url = values.get('MARIADB_MIGRATION_DATABASE_URL')
    assert database_url, 'DATABASE_URL ausente no arquivo de homologação'
    engine = create_database_engine(AppSettings(database_url=database_url))
    try:
        with engine.connect() as connection:
            version, database = connection.execute(text('SELECT VERSION(), DATABASE()')).one()
            assert database == EXPECTED_DATABASE
            assert 'MariaDB' in version and version.startswith('11.8.')
            create_statement = connection.execute(text('SHOW CREATE TABLE companies')).one()[1]
            indexes = connection.execute(text('SHOW INDEX FROM companies')).mappings().all()
            columns = connection.execute(text(
                "SELECT COLUMN_NAME, COLUMN_TYPE, DATA_TYPE, CHARACTER_SET_NAME, "
                "COLLATION_NAME, IS_NULLABLE FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'companies' "
                "AND COLUMN_NAME IN ('tenant_id', 'id') ORDER BY ORDINAL_POSITION"
            )).mappings().all()
            table = connection.execute(text(
                "SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'companies'"
            )).mappings().all()
            partial = connection.execute(text(
                "SELECT TABLE_NAME FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN "
                "('bank_accounts','bank_statements','bank_transactions') ORDER BY TABLE_NAME"
            )).scalars().all()
    finally:
        engine.dispose()

    print('SHOW_CREATE_COMPANIES=' + create_statement)
    print('COMPANY_INDEXES=' + repr([(item['Key_name'], item['Seq_in_index'], item['Column_name']) for item in indexes]))
    print('COMPANY_COLUMNS=' + repr([dict(item) for item in columns]))
    print('COMPANY_ENGINE=' + repr([dict(item) for item in table]))
    print('PARTIAL_0006_TABLES=' + repr(partial))
    assert table == [{'TABLE_NAME': 'companies', 'ENGINE': 'InnoDB'}]


def test_migration_0006_upgrade_with_matching_collation(at_0005: object) -> None:
    values = dotenv_values('.env.mariadb-migration-lab')
    database_url = values.get('MARIADB_MIGRATION_DATABASE_URL')
    assert database_url, 'DATABASE_URL ausente no arquivo de homologação'
    engine = create_database_engine(AppSettings(database_url=database_url))
    try:
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT DATABASE()')) == EXPECTED_DATABASE
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260904_0005'
            assert not connection.scalar(text(
                "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() "
                "AND TABLE_NAME IN ('bank_accounts','bank_statements','bank_transactions')"
            ))
        os.environ['DATABASE_URL'] = database_url
        get_settings.cache_clear()
        command.upgrade(Config('alembic.ini'), '20260905_0006')
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260905_0006'
            collation = connection.scalar(text(
                "SELECT TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() "
                "AND TABLE_NAME='bank_accounts'"
            ))
            foreign_keys = connection.execute(text(
                "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='bank_accounts' "
                "AND REFERENCED_TABLE_NAME='companies' GROUP BY CONSTRAINT_NAME"
            )).scalars().all()
    finally:
        engine.dispose()
        get_settings.cache_clear()
        os.environ.pop('DATABASE_URL', None)

    print('BANK_ACCOUNTS_COLLATION=' + str(collation))
    print('BANK_ACCOUNTS_PARENT_FKS=' + repr(foreign_keys))
    assert collation == 'utf8mb4_unicode_ci'
    assert foreign_keys
