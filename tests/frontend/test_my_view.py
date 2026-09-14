'''Focused static contracts for Phase 05 Minha Visão. Runtime/layout claims stay separate.'''

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def source(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_dashboard_service_is_loaded_before_application() -> None:
    html = source('index.html')
    assert 'dashboard-service.js' in html
    assert html.index('dashboard-service.js') < html.index('app.js')


def test_catalog_has_ten_permission_bound_widgets_and_five_presets() -> None:
    service = source('dashboard-service.js')
    assert len(set(re.findall(r"id: '(W\d{3})'", service))) == 10
    for permission in ('company.read', 'journal.read', 'journal.approve', 'reconciliation.manage', 'audit.read'):
        assert permission in service
    for preset in ('Visão Executiva', 'Visão Contábil', 'Visão Fiscal', 'Visão Operacional', 'Minha Visão'):
        assert preset in service


def test_dashboard_uses_central_service_and_isolates_widget_failures() -> None:
    service = source('dashboard-service.js')
    app = source('app.js')
    assert 'loadSummary(widgetIds, context)' in service
    assert 'try { return [id, await loadWidget(id, context)]; }' in service
    assert "state = error?.code === 'FORBIDDEN' ? 'FORBIDDEN' : 'ERROR'" in service
    assert 'dashboardService.loadSummary(layout.widgets, context)' in app
    assert "state?.state === 'FORBIDDEN'" in app


def test_context_change_discards_previous_dashboard_state() -> None:
    app = source('app.js')
    assert "companyId === dashboardService.allAuthorizedId" in app
    assert 'profile.companies.map((company) => company.id)' in app
    assert 'dashboardRequest += 1; dashboardModel = null; dashboardLayout = null;' in app
    assert 'requestId !== dashboardRequest' in app
    assert 'Dados anteriores descartados.' in app


def test_local_preferences_cannot_store_authority_or_operational_data() -> None:
    service = source('dashboard-service.js')
    persisted = "JSON.stringify({preset: safe.preset, widgets: safe.widgets, wide: safe.wide})"
    assert persisted in service
    assert 'permissions: safe.permissions' not in service
    assert 'accountingData' not in service
    assert 'documentContent' not in service
    assert 'token: safe.' not in service
    for name in ('app.js', 'core.js', 'api-client.js', 'mock-provider.js'):
        assert 'localStorage' not in source(name)


def test_only_existing_read_contracts_are_wired_for_future_api_mode() -> None:
    client = source('api-client.js')
    for contract in ('/reviews?limit=50', '/exceptions?limit=50', '/audit-events?limit=10'):
        assert contract in client
    assert 'dashboardReviews' in source('dashboard-service.js')
    assert 'dashboardExceptions' in source('dashboard-service.js')
    assert 'dashboardActivity' in source('dashboard-service.js')


def test_accessibility_and_responsive_dashboard_foundation() -> None:
    app = source('app.js')
    css = source('app-shell.css')
    assert 'aria-label="Widgets da Minha Visão"' in app
    assert 'aria-busy=' in app
    assert 'Não é necessário arrastar.' in app
    assert 'Nenhuma ação é necessária neste contexto.' in app
    assert '@media(max-width:1200px)' in css
    assert '@media(max-width:800px)' in css
    assert '@media(max-width:480px)' in css


def test_synthetic_provider_is_company_scoped_and_contains_no_real_identity() -> None:
    provider = source('mock-provider.js')
    assert "context.companyIds.map((id) => snapshots[id])" in provider
    assert 'synthetic-company-a' in provider
    assert 'synthetic-company-b' in provider
    assert 'example.invalid' not in provider
    assert not re.search(r'\b(?:CNPJ|CPF)\b', provider, re.I)
