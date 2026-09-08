"""Read-only diagnosis for the MariaDB downgrade dependency in revision 0002."""

from __future__ import annotations

import os

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
import pytest
from sqlalchemy import inspect, text

from serdial21.bootstrap.database import create_database_engine
from serdial21.bootstrap.settings import AppSettings, get_settings


EXPECTED_DATABASE = 'u621451815_serdial21_mig'
pytestmark = pytest.mark.mariadb_migration


@pytest.fixture
def at_0002(migration_lab_at_revision: object) -> object:
    with migration_lab_at_revision('20260903_0002') as engine:  # type: ignore[operator]
        yield engine


def test_role_binding_index_dependency_diagnosis(at_0002: object) -> None:
    values = dotenv_values('.env.mariadb-migration-lab')
    database_url = values.get('MARIADB_MIGRATION_DATABASE_URL')
    assert database_url
    engine = create_database_engine(AppSettings(database_url=database_url))
    try:
        with engine.connect() as connection:
            version, database = connection.execute(text('SELECT VERSION(), DATABASE()')).one()
            assert database == EXPECTED_DATABASE
            assert version.startswith('11.8.') and 'MariaDB' in version
            revision = connection.scalar(text('SELECT version_num FROM alembic_version'))
            tables = connection.execute(text(
                "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME"
            )).scalars().all()
            ddl = connection.execute(text('SHOW CREATE TABLE role_bindings')).one()[1]
            indexes = connection.execute(text('SHOW INDEX FROM role_bindings')).mappings().all()
            keys = connection.execute(text(
                "SELECT CONSTRAINT_NAME,TABLE_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME,ORDINAL_POSITION "
                "FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() "
                "AND (TABLE_NAME='role_bindings' OR REFERENCED_TABLE_NAME='role_bindings') "
                "ORDER BY CONSTRAINT_NAME,ORDINAL_POSITION"
            )).mappings().all()
    finally:
        engine.dispose()

    print('ALEMBIC_REVISION=' + str(revision))
    print('TABLES=' + repr(tables))
    print('ROLE_BINDINGS_DDL=' + ddl)
    print('ROLE_BINDINGS_INDEXES=' + repr([(item['Key_name'], item['Seq_in_index'], item['Column_name']) for item in indexes]))
    print('ROLE_BINDINGS_FKS=' + repr([dict(item) for item in keys]))
    assert revision == '20260903_0002'


def test_migration_0002_downgrade_and_reupgrade(at_0002: object) -> None:
    assert os.environ.get('SERDIAL21_RUN_MARIADB_MIGRATION_TESTS') == '1'
    values = dotenv_values('.env.mariadb-migration-lab')
    database_url = values.get('MARIADB_MIGRATION_DATABASE_URL')
    assert database_url
    engine = create_database_engine(AppSettings(database_url=database_url))
    try:
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT DATABASE()')) == EXPECTED_DATABASE
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260903_0002'
        os.environ['DATABASE_URL'] = database_url
        get_settings.cache_clear()
        config = Config('alembic.ini')
        command.downgrade(config, '20260903_0001')
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260903_0001'
            assert set(inspect(connection).get_table_names()) == {'alembic_version', 'tenants'}
        command.upgrade(config, '20260903_0002')
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260903_0002'
            assert 'role_bindings' in inspect(connection).get_table_names()
    finally:
        engine.dispose()
        get_settings.cache_clear()
        os.environ.pop('DATABASE_URL', None)
