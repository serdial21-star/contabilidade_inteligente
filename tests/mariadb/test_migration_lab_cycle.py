import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import text

pytestmark = pytest.mark.mariadb_migration


@pytest.fixture
def migration_engine(migration_lab_at_revision: object) -> object:
    with migration_lab_at_revision('base') as engine:  # type: ignore[operator]
        yield engine


@pytest.mark.mariadb_migration
def test_migration_lab_full_serial_cycle(migration_engine: object) -> None:
    url = dotenv_values('.env.mariadb-migration-lab').get('MARIADB_MIGRATION_DATABASE_URL')
    assert url
    previous = os.environ.get('DATABASE_URL')
    try:
        os.environ['DATABASE_URL'] = url
        config = Config('alembic.ini')
        command.upgrade(config, '20260903_0001')
        command.upgrade(config, '20260903_0002')
        command.downgrade(config, '20260903_0001')
        command.upgrade(config, '20260903_0002')
        command.upgrade(config, '20260904_0005')
        command.upgrade(config, '20260905_0006')
        with migration_engine.connect() as connection:  # type: ignore[attr-defined]
            assert connection.scalar(text("SELECT TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='bank_accounts'")) == 'utf8mb4_unicode_ci'
            assert connection.scalar(text("SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='bank_accounts' AND REFERENCED_TABLE_NAME='companies'")) > 0
        command.upgrade(config, 'head')
        command.downgrade(config, 'base')
        command.upgrade(config, 'head')
        with migration_engine.connect() as connection:  # type: ignore[attr-defined]
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260907_0009'
    finally:
        if previous is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = previous
