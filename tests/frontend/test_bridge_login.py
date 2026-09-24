'''Contrato estático do handoff de login vindo do Sistema A (ADR 0014).

Sem runtime de navegador neste ambiente: testes de conteúdo-fonte, no mesmo
padrão dos demais arquivos em tests/frontend/.
'''

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def source(name: str) -> str:
    return (APP / name).read_text(encoding='utf-8')


def test_bridge_mode_reads_token_from_hash_query_not_from_storage() -> None:
    app = source('app.js')
    assert "config.authMode === 'bridge'" in app
    assert "routeParams().get('bridge')" in app


def test_bridge_token_is_stripped_from_url_before_any_render() -> None:
    app = source('app.js')
    match = re.search(
        r"if \(config\.authMode === 'bridge'\) \{(.*?)\n\s*\}\n\s*if \(config\.authMode !== 'oidc'",
        app, re.S,
    )
    assert match, 'bloco de boot() do modo bridge não encontrado'
    block = match.group(1)
    strip_index = block.find('history.replaceState')
    bootstrap_index = block.find('bootstrapAuthenticated')
    assert strip_index != -1 and bootstrap_index != -1
    assert strip_index < bootstrap_index, 'a URL precisa ser limpa antes de usar o token'


def test_bridge_mode_reuses_the_same_authenticated_bootstrap_as_oidc() -> None:
    app = source('app.js')
    assert app.count('await bootstrapAuthenticated(') >= 2  # callback OIDC e handoff da ponte


def test_bridge_mode_shows_no_self_service_login_controls() -> None:
    app = source('app.js')
    # renderLogin só mostra o botão "Entrar" quando authMode === 'oidc', e a
    # demonstração sintética só quando authMode === 'synthetic' — 'bridge'
    # cai fora dos dois, então não deve ganhar nenhum controle próprio.
    assert "config.authMode === 'oidc' ?" in app
    assert "synthetic ? '<div class=\"demo-entry\"" in app


def test_password_and_token_are_still_not_persisted_or_logged() -> None:
    public_javascript = '\n'.join(source(name) for name in (
        'app.js', 'core.js', 'config.js', 'api-client.js', 'mock-provider.js', 'oidc-client.js',
    ))
    assert 'localStorage' not in public_javascript
    assert 'console.' not in public_javascript
