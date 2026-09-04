from pathlib import Path

from pydantic import ValidationError
import pytest

from serdial21.bootstrap.settings import AppSettings


def test_defaults_are_safe_for_local_development() -> None:
    settings = AppSettings(_env_file=None)

    assert settings.environment == 'development'
    assert settings.debug is False
    assert settings.api_prefix == '/api/v1'
    assert settings.database_url is None
    assert settings.object_storage_path == Path('.serdial21-storage')
    assert settings.resolved_database_pool_size == 5
    assert settings.resolved_database_max_overflow == 5


def test_api_prefix_is_normalized() -> None:
    settings = AppSettings(_env_file=None, api_prefix='/internal/')

    assert settings.api_prefix == '/internal'


def test_api_prefix_must_be_absolute() -> None:
    with pytest.raises(ValidationError, match='deve começar'):
        AppSettings(_env_file=None, api_prefix='api/v1')


def test_production_requires_database_url() -> None:
    with pytest.raises(ValidationError, match='DATABASE_URL'):
        AppSettings(_env_file=None, environment='production')


def test_production_rejects_debug() -> None:
    with pytest.raises(ValidationError, match='debug'):
        AppSettings(
            _env_file=None,
            environment='production',
            debug=True,
            database_url='mysql+pymysql://user:secret@db/serdial21',
        )


def test_database_url_is_redacted_from_representation() -> None:
    settings = AppSettings(
        _env_file=None,
        database_url='mysql+pymysql://user:secret@db/serdial21',
    )

    assert 'secret' not in repr(settings)


def test_database_url_uses_exact_environment_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        'DATABASE_URL',
        'mysql+pymysql://user:secret@db/serdial21',
    )

    settings = AppSettings(_env_file=None)

    assert settings.database_url is not None
    assert settings.database_url.get_secret_value().startswith('mysql+pymysql://')


def test_object_storage_path_uses_exact_environment_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv('OBJECT_STORAGE_PATH', 'var/evidence')

    settings = AppSettings(_env_file=None)

    assert settings.object_storage_path == Path('var/evidence')


def test_non_mysql_driver_is_rejected_outside_test() -> None:
    with pytest.raises(ValidationError, match='mysql.pymysql'):
        AppSettings(
            _env_file=None,
            environment='development',
            database_url='sqlite+pysqlite:///:memory:',
        )


def test_environment_profiles_have_distinct_pool_defaults() -> None:
    test_settings = AppSettings(
        _env_file=None,
        environment='test',
        database_url='sqlite+pysqlite:///:memory:',
    )
    production_settings = AppSettings(
        _env_file=None,
        environment='production',
        database_url='mysql+pymysql://user:secret@db/serdial21',
    )

    assert test_settings.resolved_database_pool_size == 1
    assert test_settings.resolved_database_max_overflow == 0
    assert production_settings.resolved_database_pool_size == 10
    assert production_settings.resolved_database_max_overflow == 20
