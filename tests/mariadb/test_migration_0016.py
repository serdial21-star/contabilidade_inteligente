'''Ciclo focado da migration 0016 (equipe interna) no Migration Lab isolado.'''

import os

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from dotenv import dotenv_values
from sqlalchemy import inspect, text


pytestmark = pytest.mark.mariadb_migration
PREVIOUS = '20260923_0015'
NEW_TABLES = {'office_team_members', 'company_team_assignments'}


def test_office_team_migration_cycle(migration_engine: object) -> None:
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
        assert not NEW_TABLES & set(inspect(migration_engine).get_table_names())
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
    assert NEW_TABLES <= set(inspector.get_table_names())
    indexes = {i['name']: i for i in inspector.get_indexes('office_team_members')}
    assert indexes['ux_office_team_members_tenant_external_reference']['unique'] is True
    uniques = {u['name'] for u in inspector.get_unique_constraints('office_team_members')}
    assert {'uq_office_team_members_tenant_id_id', 'uq_office_team_members_tenant_email'} <= uniques
    fks = {fk['name'] for fk in inspector.get_foreign_keys('company_team_assignments')}
    assert {
        'fk_company_team_assignments_tenant_company',
        'fk_company_team_assignments_tenant_member',
    } <= fks
