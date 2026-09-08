from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config

from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.database import metadata
from serdial21.bootstrap.settings import get_settings


EXPECTED_TABLES = {
    'account_locks',
    'artifact_receipts',
    'bank_accounts',
    'bank_statements',
    'bank_transactions',
    'audit_events',
    'canonical_records',
    'companies',
    'company_accesses',
    'establishments',
    'evidence_artifacts',
    'fiscal_document_items',
    'fiscal_documents',
    'import_batches',
    'import_items',
    'lineage_edges',
    'permissions',
    'role_bindings',
    'role_permissions',
    'roles',
    'tax_details',
    'tenant_memberships',
    'tenants',
    'transformation_runs',
    'validation_issues',
    'users',
    'workflow_cases',
    'workflow_work_items',
    'workflow_approval_requests',
    'authorized_effects',
    'pre_homologation_export_batches',
    'nfe_journey_checkpoints',
}


def test_model_registry_contains_approved_tables() -> None:
    load_models()

    assert set(metadata.tables) == EXPECTED_TABLES


def test_upgrade_and_downgrade_initial_revision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / 'migration.db'
    database_url = f'sqlite+pysqlite:///{database_path.as_posix()}'
    monkeypatch.setenv('SERDIAL21_ENVIRONMENT', 'test')
    monkeypatch.setenv('DATABASE_URL', database_url)
    get_settings.cache_clear()
    config = Config('alembic.ini')

    try:
        command.upgrade(config, 'head')
        assert table_names(database_path) == EXPECTED_TABLES | {'alembic_version'}
        assert permission_count(database_path) == 9
        command.check(config)

        command.downgrade(config, 'base')
        assert table_names(database_path) == {'alembic_version'}
    finally:
        get_settings.cache_clear()


def table_names(database_path: Path) -> set[str]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            'SELECT name FROM sqlite_master WHERE type = \'table\''
        ).fetchall()
    return {row[0] for row in rows}


def permission_count(database_path: Path) -> int:
    with sqlite3.connect(database_path) as connection:
        row = connection.execute('SELECT COUNT(*) FROM permissions').fetchone()
    assert row is not None
    return int(row[0])
