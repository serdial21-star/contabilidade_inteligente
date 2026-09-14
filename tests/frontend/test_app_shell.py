'''Focused static-contract tests for the native Phase 04 application shell.'''

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def source(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_application_boot_is_branded_and_protected() -> None:
    html = source('index.html')
    assert 'Inicializando ambiente seguro' in html
    assert 'aria-busy="true"' in html
    assert 'noindex,nofollow' in html
    assert "connect-src 'self'" in html
    assert "form-action 'none'" in html


def test_unauthenticated_login_delegates_credentials_to_idp() -> None:
    javascript = source('app.js')
    assert 'type="email"' not in javascript
    assert 'type="password"' not in javascript
    assert 'data-action="begin-login"' in javascript
    assert 'credenciais são tratadas somente pelo provedor' in javascript


def test_session_model_declares_all_required_states() -> None:
    core = source('core.js')
    required = {
        'BOOTING', 'UNAUTHENTICATED', 'AUTHENTICATING', 'AUTHENTICATED',
        'SESSION_EXPIRED', 'FORBIDDEN', 'NETWORK_ERROR', 'SERVER_ERROR',
    }
    assert all(f"{state}: '{state}'" in core for state in required)
    assert 'snapshot: () => Object.freeze({state, profile, mode})' in core
    assert 'cannot resume without profile' in core


def test_sidebar_uses_exact_segmented_backend_permissions() -> None:
    app = source('app.js')
    for permission in (
        'company.read', 'reconciliation.manage', 'journal.read', 'audit.read',
        'lock.manage', 'identity.manage', 'catalog.manage',
    ):
        assert permission in app
    assert 'required.some((permission) => permissions.has(permission))' in source('core.js')


def test_safe_forbidden_expired_network_and_server_copy_exists() -> None:
    app = source('app.js')
    for text in (
        'Você não possui permissão para acessar este recurso.',
        'Sua sessão expirou. Entre novamente para continuar.',
        'Não foi possível conectar',
        'Serviço temporariamente indisponível',
    ):
        assert text in app
    assert 'access denied' not in app


def test_network_calls_are_centralized_on_real_context_contract() -> None:
    assert '/identity/context?company_id=' in source('api-client.js')
    for name in ('app.js', 'core.js', 'config.js', 'mock-provider.js'):
        assert not re.search(r'\bfetch\s*\(', source(name)), name
    assert "apiBaseUrl: '/api/v1'" in source('config.js')


def test_password_and_token_are_not_persisted_or_logged() -> None:
    public_javascript = '\n'.join(source(name) for name in (
        'app.js', 'core.js', 'config.js', 'api-client.js', 'mock-provider.js',
        'oidc-client.js',
    ))
    assert 'localStorage' not in public_javascript
    assert 'console.' not in public_javascript
    assert not re.search(r'(clientSecret|privateKey|databaseUrl|password|token)\s*:', source('config.js'), re.I)
    assert 'access_token' not in re.sub(r"tokens\.access_token", '', source('oidc-client.js'))


def test_synthetic_provider_is_explicit_and_has_no_token() -> None:
    provider = source('mock-provider.js')
    config = source('config.js')
    assert "dataMode: 'synthetic'" in config
    assert 'Exemplo' in provider
    assert 'synthetic-company' in provider
    assert not re.search(r'(accessToken|bearer|password|senha)', provider, re.I)


def test_shell_has_accessible_responsive_navigation_and_logout() -> None:
    app = source('app.js')
    css = source('app-shell.css')
    assert 'aria-label="Navegação principal"' in app
    assert 'aria-expanded=' in app
    assert 'Sair do aplicativo' in app
    assert '@media(max-width:800px)' in css
    assert '.drawer-backdrop.open' in css
    assert 'aria-live="polite"' in source('index.html')


def test_prototype_brand_assets_and_required_specs_are_preserved() -> None:
    assert (APP / 'prototype.html').is_file()
    assert (APP / 'foundation.js').is_file()
    assert (APP / 'mocks.js').is_file()
    for relative in (
        'ui/tokens.css', 'ui/foundation.css',
        'ui/assets/brand/S21 assinatura principal.png',
        'ui/assets/brand/S21 assinatura vertical.png',
        'docs/AUTH_FRONTEND_INTEGRATION.md',
        'docs/FRONTEND_PERMISSION_MAP.md',
        'docs/FRONTEND_DATA_GAPS.md',
        'docs/APP_SHELL_SPEC.md',
        'app/oidc-client.js',
    ):
        assert (ROOT / relative).is_file(), relative
