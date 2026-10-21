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
    # T-0012 (ADR 0021 do B / ADR 0025 do Sistema C): só o formulário do login único S21 pede senha, e o
    # navegador a entrega direto ao serviço de login S21 (s21-login.js), nunca à API do B.
    javascript = source('app.js')
    assert javascript.count('type="email"') == 1 and javascript.count('type="password"') == 1
    assert 'function s21FormMarkup' in javascript and 's21Login.signIn(' in javascript
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
        'company.read', 'journal.read', 'audit.read',
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


def test_work_context_preference_is_minimized_and_loaded_before_application() -> None:
    html = source('index.html')
    assert html.index('work-context.js') < html.index('app.js')
    preference = source('work-context.js')
    assert "STORAGE_KEY = 's21.work-context.v1'" in preference
    for forbidden in ('tax_identifier', 'accessToken', 'filename', 'invoice', 'amount'):
        assert forbidden not in preference


def test_tax_identifier_formatter_supports_cpf_and_alphanumeric_cnpj() -> None:
    app = source('app.js')
    assert 'const formatTaxIdentifier = (value) =>' in app
    assert '/^[0-9A-Z]{12}\\d{2}$/' in app
    assert 'formatTaxIdentifier(item.detail.tax_identifier)' in app


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
def test_caddy_denies_iframe_for_application_pages() -> None:
    web = Path('deploy/web/Caddyfile').read_text(encoding='utf-8')
    host = Path('deploy/host-caddy/Caddyfile.example').read_text(encoding='utf-8')
    assert web.count("frame-ancestors 'none'") >= 2
    assert web.count('X-Frame-Options "DENY"') >= 2
    assert 'Content-Security-Policy' not in host
    assert 'X-Frame-Options "DENY"' in host


def test_t0010_s21_contabil_brand_and_no_legacy_visible_name() -> None:
    html = source('index.html')
    javascript = source('app.js')
    assert '<title>S21 Contábil</title>' in html
    assert 'S21%20Contabil%20selo.png' in html and 'S21%20selo%20mestre.png' in html
    assert 'S21%20Contabil%20selo.png' in javascript and 'S21%20selo%20mestre.png' in javascript
    # Nome antigo e "Sistema A" não aparecem em textos do aplicativo; nomes de tenant/empresa vêm de dados.
    for text in (html, javascript):
        assert 'Serdial21' not in text
        assert 'Sistema A' not in text
    for relative in ('ui/assets/brand/S21 Contabil selo.png', 'ui/assets/brand/S21 selo mestre.png'):
        assert (ROOT / relative).read_bytes()[:4] == b'\x89PNG', relative


def test_t0010_official_palette_and_dark_theme_tokens() -> None:
    tokens = (ROOT / 'ui/tokens.css').read_text(encoding='utf-8')
    assert '--brand-primary:#09265b' in tokens
    assert '--brand-gold:#d6a928' in tokens
    assert '--brand-red:#c8102e' in tokens
    assert 'html.foundation[data-theme="dark"]' in tokens
    assert 'font-size:10px' not in (ROOT / 'ui/foundation.css').read_text(encoding='utf-8')


def test_t0010_theme_toggle_and_logout_in_sidebar_footer() -> None:
    html = source('index.html')
    javascript = source('app.js')
    theme = source('theme.js')
    assert '<script src="theme.js"></script>' in html
    assert 'content="light dark"' in html
    assert 'data-action="toggle-theme"' in javascript
    assert "action === 'toggle-theme'" in javascript
    assert 'class="btn logout-button" data-action="logout"' in javascript
    # Preferência só de tema; falha de armazenamento não quebra a tela.
    assert theme.count('try {') >= 3 and "localStorage.getItem(KEY)" in theme
    assert "prefers-color-scheme: dark" in theme


def test_t0010_bridge_relaunch_keeps_tokens_out_of_web_storage() -> None:
    javascript = source('app.js')
    config = (ROOT / 'deploy/web/config.js').read_text(encoding='utf-8')
    # F5 sem crachá: volta ao S21 Administrativo para pedir outro.
    assert "bridgeRelaunchUrl: 'https://serdial21.com/admin/abrir-contabil'" in config
    assert "if (startBridgeRelaunch(returnHash, routeParams().get('r') === '1')) return;" in javascript
    assert 'location.replace(`${target}?voltar=${encodeURIComponent(marked)}`)' in javascript
    # Trava contra laço pela marca r=1 no endereço; nenhum Web Storage no aplicativo.
    assert "`${returnHash}${returnHash.includes('?') ? '&' : '?'}r=1`" in javascript
    assert 'localStorage' not in javascript and 'sessionStorage' not in javascript
    # O token sai da URL antes de qualquer chamada; a volta aceita só rota e parâmetros da lista (r e bridge ficam de fora).
    assert "history.replaceState(null, '', location.pathname); // token nunca fica na URL nem em histórico" in javascript
    assert "RETURN_PARAMS = ['company', 'document', 'fiscal', 'statement']" in javascript
    assert "/^[a-z-]{1,40}$/.test(requestedRoute || '')" in javascript
    # Ambiente de desenvolvimento não redireciona para fora.
    assert 'bridgeRelaunchUrl' not in source('config.js')


def test_t0013_s21_login_error_is_prominent_and_f5_stays_on_s21_login() -> None:
    # T-0013 (M-115 do Sistema C): erro do login S21 em destaque, e-mail mantido (senha não), F5 sem cair na ponte.
    javascript = source('app.js')
    assert "function renderLogin(message = '', tone = 'info')" in javascript
    assert "role=\"${failed ? 'alert' : 'status'}\"" in javascript and "failed ? 'Não foi possível entrar'" in javascript
    assert "renderLogin(S21_MESSAGES[error?.code] || 'Não foi possível entrar agora. Tente de novo.', 'error')" in javascript
    assert 'value="${escapeHtml(s21Email)}"' in javascript
    assert javascript.count('id="s21-password"') == 1 and 'value="${escapeHtml(s21Password' not in javascript
    # A tela fica em #entrar; a aba marcada (window.name, só um texto fixo) volta ao login S21 e à mesma tela.
    assert "history.replaceState(null, '', `${location.pathname}#entrar`)" in javascript
    assert "const S21_TAB_MARK = 's21-contabil:login-s21';" in javascript
    assert 'root.name = S21_TAB_MARK;' in javascript
    assert "if (bridgeArrival && root.name === S21_TAB_MARK) root.name = '';" in javascript
    assert "s21Return = safeReturnHash(route(), routeParams())" in javascript
    assignments = re.findall(r"root\.name\s*=(?!=)\s*([^;]+);", javascript)
    assert assignments and set(assignments) <= {'S21_TAB_MARK', "''"}
    assert 'localStorage' not in javascript and 'sessionStorage' not in javascript
