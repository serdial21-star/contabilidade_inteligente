import ast
from pathlib import Path

from serdial21.bootstrap.database import metadata
from serdial21.bootstrap.model_registry import load_models


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACCESS_CONTROL_ROOT = (
    PROJECT_ROOT / 'src' / 'serdial21' / 'modules' / 'access_control'
)
AUDIT_ROOT = PROJECT_ROOT / 'src' / 'serdial21' / 'modules' / 'audit'
INTAKE_ROOT = PROJECT_ROOT / 'src' / 'serdial21' / 'modules' / 'intake_documents'


def test_domain_does_not_import_framework_or_persistence() -> None:
    forbidden_roots = {'fastapi', 'sqlalchemy'}
    imported = imported_modules(ACCESS_CONTROL_ROOT / 'domain')

    assert imported.isdisjoint(forbidden_roots)
    assert not any('adapters' in module for module in imported)


def test_application_does_not_import_private_persistence_adapter() -> None:
    imported = imported_modules(ACCESS_CONTROL_ROOT / 'application')

    assert not any(
        module.startswith('serdial21.modules.access_control.adapters')
        for module in imported
    )


def test_audit_domain_does_not_import_framework_or_persistence() -> None:
    imported = imported_modules(AUDIT_ROOT / 'domain')

    assert imported.isdisjoint({'fastapi', 'sqlalchemy'})
    assert not any('adapters' in module for module in imported)


def test_intake_domain_does_not_import_framework_or_persistence() -> None:
    imported = imported_modules(INTAKE_ROOT / 'domain')

    assert imported.isdisjoint({'fastapi', 'sqlalchemy'})
    assert not any('adapters' in module for module in imported)


def test_all_scoped_access_tables_carry_tenant_id() -> None:
    load_models()
    tenant_scoped_tables = {
        'artifact_receipts',
        'audit_events',
        'tenant_memberships',
        'companies',
        'establishments',
        'company_accesses',
        'evidence_artifacts',
        'import_batches',
        'import_items',
        'lineage_edges',
        'roles',
        'role_permissions',
        'role_bindings',
        'transformation_runs',
        'validation_issues',
    }

    assert all(
        'tenant_id' in metadata.tables[table_name].columns
        for table_name in tenant_scoped_tables
    )


def imported_modules(directory: Path) -> set[str]:
    modules: set[str] = set()
    for source_file in directory.rglob('*.py'):
        tree = ast.parse(source_file.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
    return modules
