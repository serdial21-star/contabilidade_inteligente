'''Focused fail-closed and PKCE contract tests for the browser auth adapter.'''

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def read(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_default_auth_and_data_modes_are_explicitly_synthetic() -> None:
    config = read('config.js')
    assert "authMode: 'synthetic'" in config
    assert "dataMode: 'synthetic'" in config
    assert 'AMBIENTE DE DESENVOLVIMENTO' in read('app.js')
    assert "config.environment === 'development'" in read('app.js')


def test_oidc_configuration_is_public_empty_and_fail_closed() -> None:
    config = read('config.js')
    for field in ('issuer', 'discoveryUrl', 'clientId', 'redirectUri', 'postLogoutRedirectUri', 'audience'):
        assert re.search(rf"{field}: ''", config)
    assert 'OIDC_NOT_CONFIGURED' in read('oidc-client.js')
    assert 'Autenticação não configurada neste ambiente.' in read('app.js')


def test_authorization_code_pkce_s256_is_the_only_browser_flow() -> None:
    oidc = read('oidc-client.js')
    assert "response_type', 'code'" in oidc
    assert "grant_type: 'authorization_code'" in oidc
    assert "code_challenge_method', 'S256'" in oidc
    assert "subtle.digest(" in oidc
    assert 'implicit' not in oidc.lower()
    assert 'password' not in oidc.lower()


def test_callback_validates_state_age_and_clears_transaction() -> None:
    oidc = read('oidc-client.js')
    assert "parameters.get('state') !== transaction.state" in oidc
    assert 'MAX_TRANSACTION_AGE_MS' in oidc
    assert 'transactionStore.removeItem(TRANSACTION_KEY)' in oidc
    assert 'browserHistory.replaceState' in oidc


def test_only_pkce_transaction_not_tokens_uses_session_storage() -> None:
    oidc = read('oidc-client.js')
    assert 'root.sessionStorage' in oidc
    persisted = re.findall(r'transactionStore\.setItem\(([^\n]+)', oidc)
    assert len(persisted) == 1
    assert 'TRANSACTION_KEY' in persisted[0]
    assert 'access_token' not in persisted[0]
    assert 'refresh_token' not in oidc


def test_oidc_metadata_requires_exact_issuer_and_secure_endpoints() -> None:
    oidc = read('oidc-client.js')
    assert 'OIDC_ISSUER_MISMATCH' in oidc
    assert "endpoint.protocol !== 'https:'" in oidc
    assert "['localhost', '127.0.0.1']" in oidc
    assert 'OIDC_ENDPOINT_INSECURE' in oidc


def test_authenticated_bootstrap_calls_server_authoritative_me_first() -> None:
    app = read('app.js')
    bootstrap = app[app.index('async function bootstrapAuthenticated'):]
    assert bootstrap.index('currentApplication()') < bootstrap.index('session.establish')
    assert "currentApplication: () => request('/identity/me')" in read('api-client.js')
    assert 'renderShell();' in bootstrap


def test_401_403_logout_and_renewal_have_safe_behavior() -> None:
    app = read('app.js')
    oidc = read('oidc-client.js')
    assert "error.code === 'SESSION_EXPIRED'" in app
    assert "error.code === 'FORBIDDEN'" in app
    assert "refreshOrRenew: () => 'REAUTH_REQUIRED'" in oidc
    assert 'session.logout()' in app
    assert 'remoteLogoutEnabled' in oidc
