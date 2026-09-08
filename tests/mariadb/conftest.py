'''Guards de homologação MariaDB: runtime e laboratório nunca compartilham URL.'''

from __future__ import annotations

import os
from collections.abc import Callable, Generator
from contextlib import contextmanager
from threading import Lock

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from serdial21.bootstrap.database import create_database_engine
from serdial21.bootstrap.settings import AppSettings


RUNTIME_DATABASE = 'u621451815_serdial21_hom'
MIGRATION_DATABASE = 'u621451815_serdial21_mig'
MIGRATION_USER = 'u621451815_serdial21_mapp'
MIGRATION_HEAD = '20260908_0011'
_migration_lock = Lock()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'mariadb_runtime: requer Runtime Homologation HEAD')
    config.addinivalue_line('markers', 'mariadb_migration: requer Migration Lab descartável')
    config.addinivalue_line('markers', 'mariadb_restore: validação read-only do restore')


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    '''Falha fechada se um teste Alembic não estiver explicitamente no Lab.'''
    for item in items:
        path = str(item.path).replace('\\', '/')
        if '/tests/mariadb/' not in path:
            continue
        source = item.path.read_text(encoding='utf-8')
        changes_revision = 'command.upgrade(' in source or 'command.downgrade(' in source
        migration = item.get_closest_marker('mariadb_migration') is not None
        runtime = item.get_closest_marker('mariadb_runtime') is not None
        if changes_revision and not migration:
            raise pytest.UsageError(f'teste Alembic sem marker mariadb_migration: {item.nodeid}')
        if migration and runtime:
            raise pytest.UsageError(f'teste MariaDB com markers conflitantes: {item.nodeid}')


def _url(filename: str, key: str) -> str:
    value = dotenv_values(filename).get(key)
    if not value:
        pytest.fail(f'configuração MariaDB ausente: {filename}')
    return value


def _checked_engine(
    url: str, expected: str, opt_in: str, *, expected_user: str | None = None,
) -> Engine:
    if os.environ.get(opt_in) != '1':
        pytest.skip(f'homologação MariaDB exige {opt_in}=1')
    engine = create_database_engine(AppSettings(database_url=url))
    try:
        with engine.connect() as connection:
            version = str(connection.scalar(text('SELECT VERSION()')))
            database = connection.scalar(text('SELECT DATABASE()'))
            current_user = str(connection.scalar(text('SELECT CURRENT_USER()')))
            if not (version.startswith('11.8.') and 'MariaDB' in version and database == expected):
                pytest.fail('guard MariaDB recusou o banco configurado')
            if expected_user is not None and current_user.split('@', 1)[0] != expected_user:
                pytest.fail('guard MariaDB recusou o usuário configurado')
        return engine
    except SQLAlchemyError:
        engine.dispose()
        pytest.fail(
            'conexão MariaDB recusada; confira a configuração local sem expor credenciais',
            pytrace=False,
        )
    except BaseException:
        engine.dispose()
        raise


@pytest.fixture(scope='session')
def runtime_engine() -> Engine:
    engine = _checked_engine(
        _url('.env.mysql-homologation', 'DATABASE_URL'), RUNTIME_DATABASE,
        'SERDIAL21_RUN_MARIADB_HOMOLOGATION',
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope='session')
def migration_engine() -> Engine:
    runtime_url = _url('.env.mysql-homologation', 'DATABASE_URL')
    lab_url = _url('.env.mariadb-migration-lab', 'MARIADB_MIGRATION_DATABASE_URL')
    runtime = create_database_engine(AppSettings(database_url=runtime_url))
    try:
        with runtime.connect() as connection:
            runtime_name = connection.scalar(text('SELECT DATABASE()'))
    finally:
        runtime.dispose()
    engine = _checked_engine(
        lab_url, MIGRATION_DATABASE, 'SERDIAL21_RUN_MARIADB_MIGRATION_TESTS',
        expected_user=MIGRATION_USER,
    )
    try:
        with engine.connect() as connection:
            if connection.scalar(text('SELECT DATABASE()')) == runtime_name:
                pytest.fail('guard recusou Migration Lab igual ao Runtime')
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope='session')
def migration_lab_at_revision(
    migration_engine: Engine,
) -> Callable[[str], object]:
    '''Prepara um cenário isolado e restaura HEAD mesmo após falha.'''
    lab_url = _url('.env.mariadb-migration-lab', 'MARIADB_MIGRATION_DATABASE_URL')

    @contextmanager
    def at_revision(target: str) -> Generator[Engine, None, None]:
        if os.environ.get('SERDIAL21_RUN_MARIADB_MIGRATION_TESTS') != '1':
            pytest.fail('opt-in do Migration Lab ausente')
        with _migration_lock:
            with migration_engine.connect() as connection:
                if connection.scalar(text('SELECT DATABASE()')) != MIGRATION_DATABASE:
                    pytest.fail('Migration Lab guard recusou database')
            previous = os.environ.get('DATABASE_URL')
            scenario_error: Exception | None = None
            restore_error: Exception | None = None
            try:
                os.environ['DATABASE_URL'] = lab_url
                config = Config('alembic.ini')
                command.downgrade(config, 'base')
                if target != 'base':
                    command.upgrade(config, target)
                expected = None if target == 'base' else target
                with migration_engine.connect() as connection:
                    actual = connection.scalar(text('SELECT version_num FROM alembic_version'))
                if actual != expected:
                    pytest.fail(f'revision preparada diverge: esperada={target}, atual={actual}')
                yield migration_engine
            except Exception as error:
                scenario_error = error
            finally:
                try:
                    command.upgrade(Config('alembic.ini'), 'head')
                    with migration_engine.connect() as connection:
                        actual = connection.scalar(text('SELECT version_num FROM alembic_version'))
                    if actual != MIGRATION_HEAD:
                        raise AssertionError(f'restore não atingiu HEAD: {actual}')
                except Exception as error:
                    restore_error = error
                if previous is None:
                    os.environ.pop('DATABASE_URL', None)
                else:
                    os.environ['DATABASE_URL'] = previous
            if scenario_error is not None and restore_error is not None:
                raise ExceptionGroup('falha do cenário e do restore', [scenario_error, restore_error])
            if restore_error is not None:
                raise restore_error
            if scenario_error is not None:
                raise scenario_error

    return at_revision


def _lab_name(url: str) -> str:
    from sqlalchemy.engine import make_url
    name = make_url(url).database
    if not name:
        pytest.fail('Migration Lab sem nome de database')
    return name
