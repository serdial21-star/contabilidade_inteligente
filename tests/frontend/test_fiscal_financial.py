'''Focused static security and integration contracts for Phase 07.'''

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def source(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_intelligence_service_loads_before_application() -> None:
    html = source('index.html')
    assert html.index('intelligence-service.js') < html.index('app.js')


def test_phase07_navigation_only_exposes_implemented_surfaces() -> None:
    app = source('app.js')
    assert "id: 'fiscal', label: 'Fiscal · NF-e', permissions: ['company.read']" in app
    assert "id: 'financial', label: 'Financeiro · OFX', permissions: ['company.read']" in app
    assert "id: 'accounting', label: 'Contábil', permissions: ['journal.read']" in app
    assert 'Conciliação ainda não operacional' in app
    assert 'data-action="manual-match"' not in app


def test_existing_specialized_import_routes_are_reused() -> None:
    client = source('api-client.js')
    assert '/imports/nfe?' in client
    assert '/imports/ofx' in client
    assert "'Idempotency-Key': root.crypto.randomUUID()" in client
    assert "'X-Filename': file.name" in client
    assert 'multipart/form-data' not in client
    for name in ('app.js', 'intelligence-service.js', 'mock-provider.js'):
        assert 'fetch(' not in source(name)


def test_fiscal_ui_has_required_contract_fields_and_safe_rendering() -> None:
    app = source('app.js')
    for marker in (
        'nfe-import-form', 'accounting_date', 'period_start', 'period_end',
        'approval_expiry_date', 'fiscal-filter-form', 'open-fiscal',
        'Nenhuma NF-e encontrada.', 'detail.item_count', 'fiscal-page',
    ):
        assert marker in app
    assert 'escapeHtml(item.access_key)' in app
    assert 'escapeHtml(row.description' in app
    assert 'raw_xml' not in app
    assert 'storage_key' not in app


def test_financial_ui_preserves_credit_debit_semantics_and_masks_accounts() -> None:
    app = source('app.js')
    for marker in (
        'ofx-import-form', 'transaction-filter-form', 'Crédito +', 'Débito −',
        'row.direction', 'row.amount', 'account_masked', 'branch_masked',
        'Nenhuma transação encontrada.', 'statement-page', 'transaction-page',
    ):
        assert marker in app
    assert 'full_account' not in app


def test_context_and_logout_invalidate_phase07_state() -> None:
    app = source('app.js')
    assert 'intelligenceRequest += 1; intelligenceModel = null; importFeedback = null;' in app
    assert 'requestId !== intelligenceRequest' in app
    assert "['documents', 'inbox', 'fiscal', 'financial', 'accounting'].includes(route())" in app


def test_document_central_links_to_safe_domain_projection() -> None:
    app = source('app.js')
    assert 'operationalModel.item.fiscal_document_id' in app
    assert 'operationalModel.item.bank_statement_id' in app
    assert 'Abrir dados fiscais da NF-e' in app
    assert 'Abrir extrato e transações' in app


def test_import_feedback_and_accessibility_states_are_explicit() -> None:
    app = source('app.js')
    for marker in (
        'Importando arquivo…', 'Documento já recebido anteriormente',
        'Importação requer atenção', 'aria-live="polite"', 'role="status"',
        'type="file"', '<th>Valor</th>', 'remove-nfe-file',
        'Resultado por arquivo', 'simulação sem persistência',
        'Preenchida automaticamente:', 'PERIOD_MISMATCH',
        'Sem data contábil manual, XML fora do período é recusado',
    ):
        assert marker in app
    css = source('app-shell.css')
    assert '.amount.credit' in css
    assert '.amount.debit' in css
    assert '@media(max-width:800px)' in css


def test_nfe_selection_can_be_reviewed_before_upload() -> None:
    app = source('app.js')
    assert 'let pendingNfeFiles = [];' in app
    assert 'Você poderá conferir e remover arquivos antes de importar.' in app
    assert "const files = isNfe ? [...pendingNfeFiles]" in app
    assert 'pendingNfeFiles.splice(index, 1)' in app


def test_nfe_period_is_checked_against_xml_before_import() -> None:
    app = source('app.js')
    assert "getElementsByTagNameNS('*', 'dhEmi')" in app
    assert 'inspection.issuedDate < values.period_start' in app
    assert 'retryFiles.push(file)' in app
    assert 'Ajuste o contexto ou informe conscientemente outra data contábil.' in app


def test_synthetic_examples_are_explicitly_fictitious() -> None:
    mock = source('mock-provider.js')
    assert 'synthetic-company-a' in mock
    assert 'Produto exclusivamente fictício' in mock
    assert 'synthetic: true' in mock
    assert 'journal.propose' in mock
