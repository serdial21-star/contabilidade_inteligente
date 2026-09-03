'''Engine, sessões e transações SQLAlchemy da aplicação.'''

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Engine, MetaData, create_engine, event, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from serdial21.bootstrap.settings import AppSettings


NAMING_CONVENTION: dict[str, str] = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata


class UTCDateTime(TypeDecorator[datetime]):
    '''Persiste UTC sem offset no MySQL e devolve datetime aware no Python.'''

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: Any,
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('datetime técnico deve possuir timezone')
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(
        self,
        value: datetime | None,
        dialect: Any,
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class DatabaseNotConfiguredError(RuntimeError):
    '''Indica ausência de DATABASE_URL sem expor seu conteúdo.'''


def normalized_database_url(settings: AppSettings) -> URL:
    if settings.database_url is None:
        raise DatabaseNotConfiguredError('DATABASE_URL não configurada')

    url = make_url(settings.database_url.get_secret_value())
    if url.get_backend_name() == 'mysql':
        url = url.update_query_dict({'charset': 'utf8mb4'})
    return url


def create_database_engine(settings: AppSettings) -> Engine:
    '''Cria engine sem estabelecer conexão antecipada.'''

    url = normalized_database_url(settings)
    common_options: dict[str, Any] = {
        'pool_pre_ping': True,
        'pool_reset_on_return': 'rollback',
    }

    if url.get_backend_name() == 'sqlite':
        engine = create_engine(
            url,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            **common_options,
        )
        event.listen(engine, 'connect', _enable_sqlite_foreign_keys)
        return engine

    connect_args = {
        'connect_timeout': settings.database_connect_timeout_seconds,
        'read_timeout': settings.database_read_timeout_seconds,
        'write_timeout': settings.database_write_timeout_seconds,
        'init_command': 'SET time_zone = ' + chr(39) + '+00:00' + chr(39),
    }
    return create_engine(
        url,
        pool_size=settings.resolved_database_pool_size,
        max_overflow=settings.resolved_database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        pool_recycle=settings.database_pool_recycle_seconds,
        connect_args=connect_args,
        **common_options,
    )


def _enable_sqlite_foreign_keys(
    dbapi_connection: Any,
    _: Any,
) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute('PRAGMA foreign_keys=ON')
    finally:
        cursor.close()


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


@contextmanager
def session_scope(
    factory: sessionmaker[Session],
) -> Generator[Session, None, None]:
    '''Confirma a unidade de trabalho ou executa rollback em qualquer falha.'''

    session = factory()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_connection(engine: Engine) -> bool:
    '''Executa uma consulta mínima sem propagar detalhes de conexão.'''

    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return True
    except (SQLAlchemyError, OSError):
        return False


@dataclass
class DatabaseRuntime:
    '''Recursos de banco pertencentes ao ciclo de vida da aplicação.'''

    engine: Engine | None
    session_factory: sessionmaker[Session] | None

    @classmethod
    def from_settings(cls, settings: AppSettings) -> 'DatabaseRuntime':
        if settings.database_url is None:
            return cls(engine=None, session_factory=None)
        engine = create_database_engine(settings)
        return cls(
            engine=engine,
            session_factory=create_session_factory(engine),
        )

    @property
    def configured(self) -> bool:
        return self.engine is not None

    def check(self) -> bool:
        if self.engine is None:
            return False
        return check_database_connection(self.engine)

    def dispose(self) -> None:
        if self.engine is not None:
            self.engine.dispose()
