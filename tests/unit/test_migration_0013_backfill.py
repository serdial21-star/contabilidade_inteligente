from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = runpy.run_path(str(
    ROOT / 'alembic/versions/20260916_0013_company_banking_document_metadata.py'
))


def test_journey_search_backfill_matches_new_checkpoint_search_fields() -> None:
    values = MIGRATION['_journey_search_values']({
        'lines': [{'account_version_id': 'account-1'}],
        'plan': {'accounts': [
            {'id': 'account-1', 'code': '1.1.01', 'name': 'Caixa'},
            {'id': 'account-2', 'code': '2.1.01', 'name': 'Fornecedores'},
        ]},
        'evaluation': {'proposal': {'rule_version_id': 'rule-1'}},
        'sources': [{'source_type': 'FiscalDocument'}],
        'revision': {'accounting_date': '2026-09-16'},
    }, {'rule-1': ('Compra de mercadoria',)})

    assert values == {
        'account_search': '1.1.01 caixa',
        'rule_search': 'rule-1 compra de mercadoria',
        'source_search': 'FiscalDocument',
        'accounting_date_index': '2026-09-16',
    }


def test_journey_search_backfill_tolerates_missing_optional_snapshots() -> None:
    assert MIGRATION['_journey_search_values']({}) == {
        'account_search': None,
        'rule_search': None,
        'source_search': None,
        'accounting_date_index': None,
    }
