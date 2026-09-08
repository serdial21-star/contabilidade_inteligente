"""Opt-in reset of the dedicated MariaDB homologation database via Alembic."""

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


def test_reset_dedicated_database_to_base(migration_lab_at_revision: object) -> None:
    assert os.environ.get('SERDIAL21_RUN_MARIADB_MIGRATION_TESTS') == '1'
    values = dotenv_values('.env.mariadb-migration-lab')
    database_url = values.get('MARIADB_MIGRATION_DATABASE_URL')
    assert database_url, 'DATABASE_URL ausente no arquivo de homologação'
    with migration_lab_at_revision('head') as engine:  # type: ignore[operator]
        with engine.connect() as connection:
            version, database = connection.execute(text('SELECT VERSION(), DATABASE()')).one()
            assert database == EXPECTED_DATABASE
            assert version.startswith('11.8.') and 'MariaDB' in version
            table_names = [name for name in inspect(connection).get_table_names() if name != 'alembic_version']
            counts = {
                name: connection.scalar(text(f'SELECT COUNT(*) FROM `{name}`'))
                for name in table_names
            }
            assert all(
                count == (9 if name == 'permissions' else 0)
                for name, count in counts.items()
            ), counts
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260907_0009'
        os.environ['DATABASE_URL'] = database_url
        get_settings.cache_clear()
        command.downgrade(Config('alembic.ini'), 'base')
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT DATABASE()')) == EXPECTED_DATABASE
            assert inspect(connection).get_table_names() == ['alembic_version']
        command.upgrade(Config('alembic.ini'), 'head')
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '20260907_0009'
        get_settings.cache_clear()
        os.environ.pop('DATABASE_URL', None)
