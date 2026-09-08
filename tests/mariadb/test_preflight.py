'''Pre-flight read-only que recusa alvo diferente do banco descartável autorizado.'''

import pytest
from dotenv import dotenv_values
from sqlalchemy import text

from serdial21.bootstrap.database import create_database_engine
from serdial21.bootstrap.settings import AppSettings


_config = dotenv_values('.env.mysql-homologation')

pytestmark = [pytest.mark.mariadb_runtime, pytest.mark.skipif(
    _config.get('SERDIAL21_RUN_MARIADB_HOMOLOGATION') != '1',
    reason='homologação MariaDB exige opt-in explícito',
)]


def test_mariadb_homologation_preflight_is_read_only() -> None:
    url = _config.get('DATABASE_URL')
    assert url
    engine = create_database_engine(AppSettings(database_url=url))
    try:
        with engine.connect() as connection:
            version = str(connection.scalar(text('SELECT VERSION()')))
            assert 'MariaDB' in version and version.startswith('11.8.')
            assert connection.scalar(text('SELECT DATABASE()')) == 'u621451815_serdial21_hom'
            assert connection.scalar(text('SELECT CURRENT_USER()'))
            assert connection.scalar(text('SELECT @@session.time_zone')) == '+00:00'
            assert connection.scalar(text('SELECT @@character_set_connection')) == 'utf8mb4'
            assert str(connection.scalar(text('SELECT @@collation_connection'))).startswith('utf8mb4_')
    finally:
        engine.dispose()
