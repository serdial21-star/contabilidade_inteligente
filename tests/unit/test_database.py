from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, func, select
from sqlalchemy.exc import SQLAlchemyError

from serdial21.bootstrap.database import (
    DatabaseRuntime,
    UTCDateTime,
    check_database_connection,
    create_database_engine,
    create_session_factory,
    normalized_database_url,
    session_scope,
)
from serdial21.bootstrap.settings import AppSettings


def mysql_settings() -> AppSettings:
    return AppSettings(
        _env_file=None,
        environment='development',
        database_url='mysql+pymysql://user:secret@db/serdial21?charset=latin1',
    )


def test_mysql_url_always_uses_utf8mb4_and_hides_password() -> None:
    url = normalized_database_url(mysql_settings())

    assert url.query['charset'] == 'utf8mb4'
    assert 'secret' not in str(url)


def test_mysql_engine_has_prudent_pool_and_connection_options() -> None:
    settings = mysql_settings()
    expected_engine = Mock()

    with patch(
        'serdial21.bootstrap.database.create_engine',
        return_value=expected_engine,
    ) as create_engine_mock:
        engine = create_database_engine(settings)

    url = create_engine_mock.call_args.args[0]
    options = create_engine_mock.call_args.kwargs
    assert engine is expected_engine
    assert url.query['charset'] == 'utf8mb4'
    assert options['pool_pre_ping'] is True
    assert options['pool_reset_on_return'] == 'rollback'
    assert options['pool_size'] == 5
    assert options['max_overflow'] == 5
    assert options['pool_timeout'] == 10
    assert options['pool_recycle'] == 1800
    assert options['connect_args'] == {
        'connect_timeout': 10,
        'read_timeout': 30,
        'write_timeout': 30,
        'init_command': 'SET time_zone = ' + chr(39) + '+00:00' + chr(39),
    }


def test_session_scope_commits_successful_work() -> None:
    engine = create_engine('sqlite+pysqlite:///:memory:')
    table = build_test_table(engine)
    factory = create_session_factory(engine)

    with session_scope(factory) as session:
        session.execute(table.insert().values(id=1))

    with engine.connect() as connection:
        count = connection.scalar(select(func.count()).select_from(table))
    assert count == 1
    engine.dispose()


def test_session_scope_rolls_back_failed_work() -> None:
    engine = create_engine('sqlite+pysqlite:///:memory:')
    table = build_test_table(engine)
    factory = create_session_factory(engine)

    with pytest.raises(RuntimeError, match='forced failure'):
        with session_scope(factory) as session:
            session.execute(table.insert().values(id=1))
            raise RuntimeError('forced failure')

    with engine.connect() as connection:
        count = connection.scalar(select(func.count()).select_from(table))
    assert count == 0
    engine.dispose()


def test_database_health_returns_false_without_leaking_exception() -> None:
    engine = Mock()
    engine.connect.side_effect = SQLAlchemyError('host and credentials')

    assert check_database_connection(engine) is False


def test_runtime_without_url_is_explicitly_unconfigured() -> None:
    runtime = DatabaseRuntime.from_settings(AppSettings(_env_file=None))

    assert runtime.configured is False
    assert runtime.check() is False


def test_utc_datetime_rejects_naive_values() -> None:
    column_type = UTCDateTime()

    with pytest.raises(ValueError, match='timezone'):
        column_type.process_bind_param(datetime(2026, 9, 3, 10, 0), None)


def test_utc_datetime_normalizes_write_and_restores_aware_read() -> None:
    column_type = UTCDateTime()
    source = datetime(
        2026,
        9,
        3,
        10,
        0,
        tzinfo=timezone(timedelta(hours=-3)),
    )

    stored = column_type.process_bind_param(source, None)
    restored = column_type.process_result_value(stored, None)

    assert stored == datetime(2026, 9, 3, 13, 0)
    assert restored == datetime(2026, 9, 3, 13, 0, tzinfo=UTC)


def build_test_table(engine: object) -> Table:
    metadata = MetaData()
    table = Table('test_items', metadata, Column('id', Integer, primary_key=True))
    metadata.create_all(engine)
    return table
