'''Inspeciona somente metadados seguros do Runtime `_hom` confirmado.'''

from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import text

from serdial21.bootstrap.database import create_database_engine
from serdial21.bootstrap.settings import AppSettings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / '.env.mysql-homologation'
EXPECTED_DATABASE = 'u621451815_serdial21_hom'
COUNTED_TABLES = ('tenants', 'companies', 'users', 'audit_events')


def main() -> int:
    url = dotenv_values(CONFIG_PATH).get('DATABASE_URL')
    if not url:
        raise RuntimeError('configuração de homologação ausente')

    engine = create_database_engine(AppSettings(_env_file=None, database_url=url))
    try:
        with engine.connect() as connection:
            database = str(connection.scalar(text('SELECT DATABASE()')))
            if database != EXPECTED_DATABASE:
                raise RuntimeError('inspeção recusou alvo diferente do `_hom`')

            version = str(connection.scalar(text('SELECT VERSION()')))
            revision = str(connection.scalar(text(
                'SELECT version_num FROM alembic_version'
            )))
            table_count = int(connection.scalar(text(
                'SELECT COUNT(*) FROM information_schema.tables '
                'WHERE table_schema = DATABASE()'
            )) or 0)
            ssl_row = connection.execute(text("SHOW STATUS LIKE 'Ssl_cipher'")).one()
            existing = {
                str(row[0])
                for row in connection.execute(text(
                    'SELECT table_name FROM information_schema.tables '
                    'WHERE table_schema = DATABASE()'
                ))
            }

            print(f'DATABASE={database}')
            print(f'VERSION={version}')
            print(f'ALEMBIC={revision}')
            print(f'TABLES={table_count}')
            print(f'TLS={"ACTIVE" if ssl_row[1] else "INACTIVE"}')
            for table_name in COUNTED_TABLES:
                if table_name in existing:
                    count = int(connection.scalar(text(
                        f'SELECT COUNT(*) FROM {table_name}'
                    )) or 0)
                    print(f'COUNT_{table_name.upper()}={count}')
    finally:
        engine.dispose()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
