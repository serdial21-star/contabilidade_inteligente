'''Focused static security and integration contracts for Phase 06.'''

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def source(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_operational_service_loads_before_application() -> None:
    html = source('index.html')
    assert html.index('operational-service.js') < html.index('app.js')


def test_navigation_exposes_phase06_areas_without_reopening_later_phases() -> None:
    app = source('app.js')
    assert "id: 'inbox', label: 'Caixa de entrada'" in app
    assert "id: 'documents', label: 'Documentos'" in app
    assert "id: 'clients', label: 'Empresas'" in app
    assert "id: 'fiscal', label: 'Fiscal · NF-e', permissions: ['company.read']" in app
    assert "id: 'financial', label: 'Financeiro · OFX', permissions: ['company.read']" in app


def test_document_contracts_are_centralized_and_server_scoped() -> None:
    client = source('api-client.js')
    assert '/operations/companies/${encodeURIComponent(companyId)}/documents?' in client
    assert '/documents/${encodeURIComponent(documentId)}' in client
    assert '/documents/summary' in client
    for name in ('app.js', 'operational-service.js', 'mock-provider.js'):
        assert 'fetch(' not in source(name)


def test_context_switch_invalidates_operational_state() -> None:
    app = source('app.js')
    assert 'operationalRequest += 1; operationalModel = null;' in app
    assert 'requestId !== operationalRequest' in app
    assert 'Dados anteriores descartados.' in app


def test_untrusted_metadata_is_escaped_and_storage_is_not_rendered() -> None:
    app = source('app.js')
    assert 'escapeHtml(item.filename)' in app
    assert 'escapeHtml(issue.code)' in app
    assert 'item.storage_key' not in app
    assert 'item.artifact_id' not in app
    assert 'innerHTML = item.filename' not in app


def test_generic_upload_gap_is_explicit_and_does_not_fake_success() -> None:
    app = source('app.js')
    assert 'Upload documental genérico ainda não disponível' in app
    assert 'não inventa parâmetros contábeis' in app
    assert 'UPLOAD COMPLETE' not in app


def test_operational_views_have_filters_pagination_empty_error_and_accessibility() -> None:
    app = source('app.js')
    for marker in ('document-filter-form', 'document-page', 'Nenhum documento encontrado', 'role="alert"', 'aria-busy="true"'):
        assert marker in app
    css = source('app-shell.css')
    assert '.table-wrap{overflow-x:auto}' in css
    assert '.operational-cards{grid-template-columns:1fr}' in css
