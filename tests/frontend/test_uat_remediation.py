from pathlib import Path


ROOT = Path(__file__).parents[2]
APP = (ROOT / 'app/app.js').read_text(encoding='utf-8')
CSS = (ROOT / 'app/app-shell.css').read_text(encoding='utf-8')


def test_supported_deep_link_is_preserved_in_synthetic_boot() -> None:
    assert "location.hash = authorizedRoute(profile)" in APP
    assert "if (safe !== route()) { location.hash = safe; return; }" in APP
    assert "location.hash = 'overview'; renderShell();" not in APP


def test_import_feedback_is_screen_scoped_and_filters_clear_it() -> None:
    assert "importFeedback.scope !== route()" in APP
    assert "importFeedback = {scope: route(), state: 'ERROR'" in APP
    assert "if (event.target.id === 'fiscal-filter-form')" in APP
    assert "'clear-fiscal-filters'" in APP


def test_nfe_multi_file_folder_help_and_optional_accounting_date() -> None:
    assert 'name="file" type="file" accept=".xml,application/xml,text/xml" multiple' in APP
    assert 'name="folder" type="file"' in APP
    assert 'webkitdirectory directory' in APP
    assert 'Data contábil (opcional)' in APP
    assert 'approval-expiry-help' in APP


def test_filter_reset_and_review_detail_contracts() -> None:
    for action in (
        'clear-document-filters', 'clear-fiscal-filters',
        'clear-transaction-filters', 'clear-proposal-filters',
    ):
        assert action in APP
    assert 'accountingService.proposalActivity' in APP
    assert 'Registrada de' in APP and 'created_from' in APP
    assert 'Postada:' in APP and 'document_number' in APP


def test_dashboard_and_decision_line_responsive_contracts() -> None:
    assert "widget.id === 'W004' ? '#inbox'" in APP
    assert 'grid-template-columns:repeat(4,minmax(0,1fr))' in CSS
    assert '@media(min-width:1100px)' in CSS
    assert 'grid-auto-flow:column' in CSS
    assert '@media(max-width:768px){.dashboard-grid{grid-template-columns:1fr}' in CSS
