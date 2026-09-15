from pathlib import Path


ROOT = Path(__file__).parents[2]  # repository root


def test_decision_line_is_wired_to_supported_details_and_escapes_content() -> None:
    app = (ROOT / 'app/app.js').read_text(encoding='utf-8')
    api = (ROOT / 'app/api-client.js').read_text(encoding='utf-8')
    css = (ROOT / 'app/app-shell.css').read_text(encoding='utf-8')

    assert '/decision-lines/${encodeURIComponent(rootType)}/${encodeURIComponent(id)}' in api
    assert "'DOCUMENT'" in app
    assert "'FISCAL_DOCUMENT'" in app
    assert "'BANK_STATEMENT'" in app
    assert "'ACCOUNTING_PROPOSAL'" in app
    assert 'escapeHtml(event.actor_display_name)' in app
    assert 'escapeHtml(event.title)' in app
    assert 'escapeHtml(event.description)' in app
    assert "event.evidence_kind === 'DOMAIN_DERIVED_EVENT'" in app
    assert '.decision-line' in css and '.decision-event' in css


def test_decision_line_client_has_no_write_method_or_raw_audit_rendering() -> None:
    app = (ROOT / 'app/app.js').read_text(encoding='utf-8')
    api = (ROOT / 'app/api-client.js').read_text(encoding='utf-8')

    decision_contract = api[api.index('decisionLine:'):api.index('accountingCatalog:')]
    assert "method: 'POST'" not in decision_contract
    assert 'before_state' not in app
    assert 'after_state' not in app
    assert 'storage_key' not in app
