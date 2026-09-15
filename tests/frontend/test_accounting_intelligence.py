'''Focused static security and integration contracts for Phase 08.'''

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def source(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_accounting_service_loads_before_application() -> None:
    html = source('index.html')
    assert html.index('accounting-service.js') < html.index('app.js')


def test_accounting_routes_are_scoped_and_server_paginated() -> None:
    client = source('api-client.js')
    for route in (
        '/accounting-proposals?', '/accounting-catalog', '/accounting-rules/',
        '/accounting-accounts/', '/reviews/',
    ):
        assert route in client
    assert 'queryString(filters)' in client
    assert "'Idempotency-Key': root.crypto.randomUUID()" in client
    assert "response.status === 423" in client


def test_proposal_ui_distinguishes_automation_from_professional_decision() -> None:
    app = source('app.js')
    for marker in (
        'PROPOSTA CONTÁBIL · SUGESTÃO DETERMINÍSTICA',
        'AUTOMATION ≠ PROFESSIONAL DECISION', 'Aprovar internamente',
        'Rejeitar proposta', 'NÃO BALANCEADO', 'Totais autorizados pelo backend',
        'accounting-decision-form', 'revision_hash', 'RESOURCE_LOCKED',
    ):
        assert marker in app
    assert 'detail.lines.map' in app
    assert 'reduce(' not in app[app.index('function proposalDetailMarkup'):app.index('function catalogMarkup')]


def test_rule_and_mapping_views_are_read_only_and_explanatory() -> None:
    app = source('app.js')
    assert 'Regras, contas e mapeamentos' in app
    assert 'Regra determinística publicada' in app
    assert 'Escrita de regras e mapeamentos está adiada' in app
    assert 'sem expressão executável' in app
    assert 'rule-builder' not in app


def test_phase08_state_is_invalidated_on_company_change_and_logout() -> None:
    app = source('app.js')
    assert 'accountingRequest += 1; accountingModel = null' in app
    assert 'requestId !== accountingRequest' in app
    assert "['documents', 'inbox', 'fiscal', 'financial', 'accounting'].includes(route())" in app


def test_accounting_visuals_are_responsive_and_accessible() -> None:
    app = source('app.js')
    css = source('app-shell.css')
    assert 'aria-label="Áreas contábeis"' in app
    assert 'aria-labelledby="decision-title"' in app
    assert 'name="confirmed" required' in app
    assert '.proposal-priority' in css
    assert '.intelligence-card' in css
    assert '.proposal-priority{grid-template-columns:1fr}' in css


def test_synthetic_accounting_data_is_explicit_and_company_scoped() -> None:
    mock = source('mock-provider.js')
    assert 'Regra NF-e exclusivamente fictícia' in mock
    assert "companyId === 'synthetic-company-a'" in mock
    assert "companyId !== 'synthetic-company-a'" in mock
    assert 'syntheticProposalStatus' in mock
