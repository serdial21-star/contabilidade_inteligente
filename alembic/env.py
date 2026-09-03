'''Ambiente Alembic do Serdial21.'''

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import URL

from serdial21.bootstrap.database import metadata, normalized_database_url
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import get_settings


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_models()
target_metadata = metadata


def require_database_url() -> URL:
    settings = get_settings()
    if settings.database_url is None:
        raise RuntimeError(
            'DATABASE_URL deve estar configurada para executar migrations'
        )
    return normalized_database_url(settings)


def run_migrations_offline() -> None:
    context.configure(
        url=require_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    settings = get_settings()
    url = require_database_url()
    connect_args = {}
    if url.get_backend_name() == 'mysql':
        connect_args = {
            'connect_timeout': settings.database_connect_timeout_seconds,
            'read_timeout': settings.database_read_timeout_seconds,
            'write_timeout': settings.database_write_timeout_seconds,
            'init_command': (
                'SET time_zone = ' + chr(39) + '+00:00' + chr(39)
            ),
        }
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
