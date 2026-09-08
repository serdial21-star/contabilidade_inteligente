'''Ciclo controlado da migration 0009, limitado ao banco homologação autorizado.'''

import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import text


_config = dotenv_values('.env.mariadb-migration-lab')
pytestmark = pytest.mark.mariadb_migration


@pytest.fixture
def migration_engine(migration_lab_at_revision: object) -> object:
    with migration_lab_at_revision('head') as engine:  # type: ignore[operator]
        yield engine


def test_account_lock_migration_downgrade_and_reupgrade(migration_engine: object) -> None:
    url = _config.get('MARIADB_MIGRATION_DATABASE_URL')
    assert url
    original = os.environ.get('DATABASE_URL')
    try:
        with migration_engine.connect() as connection:  # type: ignore[attr-defined]
            assert connection.scalar(text('SELECT DATABASE()')) == 'u621451815_serdial21_mig'
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260907_0009'
        os.environ['DATABASE_URL'] = url
        command.downgrade(Config('alembic.ini'), '20260906_0008')
        with migration_engine.connect() as connection:  # type: ignore[attr-defined]
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260906_0008'
            assert connection.scalar(text("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='account_locks'")) == 0
        command.upgrade(Config('alembic.ini'), '20260907_0009')
        with migration_engine.connect() as connection:  # type: ignore[attr-defined]
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260907_0009'
            assert connection.scalar(text("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='account_locks'")) == 1
    finally:
        if original is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = original
