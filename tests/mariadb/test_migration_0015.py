'''Ciclo focado da migration 0015 no Migration Lab isolado.'''

import os

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from dotenv import dotenv_values
from sqlalchemy import inspect, text


pytestmark = pytest.mark.mariadb_migration
PREVIOUS = '20260916_0014'


def test_company_external_reference_migration_cycle(migration_engine: object) -> None:
    url = dotenv_values('.env.mariadb-migration-lab').get('MARIADB_MIGRATION_DATABASE_URL')
    assert url
    previous_url = os.environ.get('DATABASE_URL')
    config = Config('alembic.ini')
    try:
        os.environ['DATABASE_URL'] = url
        command.upgrade(config, 'head')
        current_head = ScriptDirectory.from_config(config).get_current_head()
        assert current_head is not None
        _assert_head(migration_engine, current_head)
        _assert_schema(migration_engine)
        command.downgrade(config, PREVIOUS)
        _assert_head(migration_engine, PREVIOUS)
        columns = {column['name'] for column in inspect(migration_engine).get_columns('companies')}
        assert not {'external_system', 'external_type', 'external_id'} & columns
        command.upgrade(config, 'head')
        _assert_head(migration_engine, current_head)
        _assert_schema(migration_engine)
    finally:
        command.upgrade(config, 'head')
        if previous_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = previous_url


def _assert_head(engine: object, revision: str) -> None:
    with engine.connect() as connection:  # type: ignore[attr-defined]
        assert connection.scalar(text('SELECT DATABASE()')) == 'u621451815_serdial21_mig'
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == revision


def _assert_schema(engine: object) -> None:
    inspector = inspect(engine)
    columns = {column['name']: column for column in inspector.get_columns('companies')}
    for name in ('external_system', 'external_type', 'external_id'):
        assert columns[name]['nullable'] is True
    indexes = {index['name']: index for index in inspector.get_indexes('companies')}
    assert indexes['ux_companies_tenant_external_reference']['unique'] is True
