import os

import pytest
from dotenv import dotenv_values
from sqlalchemy import inspect, text

from serdial21.bootstrap.database import create_database_engine
from serdial21.bootstrap.settings import AppSettings, get_settings


_config = dotenv_values('.env.mysql-homologation')
pytestmark = [pytest.mark.mariadb_runtime, pytest.mark.skipif(
    _config.get('SERDIAL21_RUN_MARIADB_HOMOLOGATION') != '1',
    reason='homologação MariaDB exige SERDIAL21_RUN_MARIADB_HOMOLOGATION=1',
)]


def test_account_lock_migration_schema() -> None:
    url = _config.get('DATABASE_URL')
    assert url
    engine = create_database_engine(AppSettings(database_url=url))
    try:
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT DATABASE()')) == 'u621451815_serdial21_hom'
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260907_0009'
            assert connection.scalar(text("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='account_locks'")) == 'InnoDB'
            assert connection.scalar(text("SELECT TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='account_locks'")) == 'utf8mb4_unicode_ci'
            assert any(item['name'] == 'uq_account_locks_active_scope' for item in inspector.get_unique_constraints('account_locks'))
    finally:
        engine.dispose()
        get_settings.cache_clear()
        os.environ.pop('DATABASE_URL', None)
