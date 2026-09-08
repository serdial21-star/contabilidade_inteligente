'''Validação read-only do backup restaurado no Lab autorizado.'''

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from dotenv import dotenv_values
import pytest
from sqlalchemy import Engine, inspect, select, text
from sqlalchemy.orm import Session

from serdial21.bootstrap.database import create_database_engine
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.locks.adapters.outbound.persistence.models import AccountLockModel
from serdial21.modules.locks.adapters.outbound.persistence.repositories import (
    SQLAlchemyAccountLockRepository,
)


RUNTIME_DATABASE = 'u621451815_serdial21_hom'
RESTORE_DATABASE = 'u621451815_serdial21_mig'
HEAD = '20260907_0009'
pytestmark = pytest.mark.mariadb_restore


def _engine(filename: str, key: str, expected_database: str) -> Engine:
    url = dotenv_values(filename).get(key)
    if not url:
        pytest.fail(f'configuração ausente: {filename}')
    engine = create_database_engine(AppSettings(database_url=url))
    with engine.connect() as connection:
        actual = connection.scalar(text('SELECT DATABASE()'))
        version = str(connection.scalar(text('SELECT VERSION()')))
        if actual != expected_database or not version.startswith('11.8.8-MariaDB'):
            engine.dispose()
            pytest.fail('guard recusou banco ou versão inesperada')
    return engine


def _table_counts(engine: Engine) -> dict[str, int]:
    inspector = inspect(engine)
    result: dict[str, int] = {}
    with engine.connect() as connection:
        for table in inspector.get_table_names():
            if not table.replace('_', '').isalnum():
                pytest.fail('identificador de tabela inesperado')
            result[table] = int(connection.scalar(text(f'SELECT COUNT(*) FROM `{table}`')))
    return result


def _schema_signature(engine: Engine) -> str:
    query = text(
        'SELECT TABLE_NAME, ENGINE, TABLE_COLLATION FROM information_schema.TABLES '
        'WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME'
    )
    columns = text(
        'SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT '
        'FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() '
        'ORDER BY TABLE_NAME,ORDINAL_POSITION'
    )
    constraints = text(
        'SELECT TABLE_NAME,CONSTRAINT_NAME,CONSTRAINT_TYPE '
        'FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA=DATABASE() '
        'ORDER BY TABLE_NAME,CONSTRAINT_NAME'
    )
    indexes = text(
        'SELECT TABLE_NAME,INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME '
        'FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() '
        'ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX'
    )
    with engine.connect() as connection:
        payload = [
            [tuple(row) for row in connection.execute(statement)]
            for statement in (query, columns, constraints, indexes)
        ]
    return hashlib.sha256(
        json.dumps(payload, default=str, ensure_ascii=True).encode()
    ).hexdigest()


def _row_digest(rows: list[tuple[Any, ...]]) -> str:
    payload = json.dumps(rows, default=str, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def test_restored_schema_counts_and_orm_reads_match_runtime() -> None:
    if os.environ.get('SERDIAL21_RUN_MARIADB_RESTORE_VALIDATION') != '1':
        pytest.skip('validação de restore exige opt-in explícito')
    runtime = _engine('.env.mysql-homologation', 'DATABASE_URL', RUNTIME_DATABASE)
    restored = _engine(
        '.env.mariadb-migration-lab', 'MARIADB_MIGRATION_DATABASE_URL', RESTORE_DATABASE,
    )
    try:
        runtime_counts = _table_counts(runtime)
        restored_counts = _table_counts(restored)
        if runtime_counts != restored_counts:
            pytest.fail('contagens Runtime/Restore divergiram')
        if _schema_signature(runtime) != _schema_signature(restored):
            pytest.fail('estrutura Runtime/Restore divergiu')

        with runtime.connect() as source, restored.connect() as target:
            if source.scalar(text('SELECT version_num FROM alembic_version')) != HEAD:
                pytest.fail('Runtime não está em HEAD')
            if target.scalar(text('SELECT version_num FROM alembic_version')) != HEAD:
                pytest.fail('Restore não está em HEAD')
            source_locks = [tuple(row) for row in source.execute(text(
                'SELECT id,tenant_id,scope_fingerprint,active_marker,status '
                'FROM account_locks ORDER BY id'
            ))]
            target_locks = [tuple(row) for row in target.execute(text(
                'SELECT id,tenant_id,scope_fingerprint,active_marker,status '
                'FROM account_locks ORDER BY id'
            ))]
            if _row_digest(source_locks) != _row_digest(target_locks):
                pytest.fail('integridade de AccountLock divergiu')

        with Session(restored) as session:
            audit = session.scalar(select(AuditEventModel).limit(1))
            if restored_counts['audit_events'] and audit is None:
                pytest.fail('AuditEvent restaurado não pôde ser lido via ORM')
            if audit is not None:
                for payload in (audit.before_state, audit.after_state):
                    if payload is not None and not isinstance(payload, dict):
                        pytest.fail('payload JSON de AuditEvent inválido')

            lock = session.scalar(select(AccountLockModel).limit(1))
            if restored_counts['account_locks'] and lock is None:
                pytest.fail('AccountLock restaurado não pôde ser lido via ORM')
            if lock is not None:
                restored_lock = SQLAlchemyAccountLockRepository(session).get(
                    lock.tenant_id, lock.id,
                )
                if restored_lock is None:
                    pytest.fail('repositório não leu AccountLock restaurado')
    finally:
        runtime.dispose()
        restored.dispose()
