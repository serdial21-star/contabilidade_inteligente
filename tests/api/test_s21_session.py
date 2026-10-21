'''T-0014 (D-059 do Sistema C): sessão do login S21 que sobrevive ao F5, com a renovação num cookie HttpOnly.'''
from __future__ import annotations

from dataclasses import dataclass, field

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from pydantic import HttpUrl
import pytest

from serdial21.modules.identity.application.ports.session import RefreshedSession, SessionRefreshError
from tests.api.test_identity_security import IdentityFixture, _headers, identity  # noqa: F401 - fixture
from tests.api.test_s21_login import S21_URL, s21, s21_token  # noqa: F401 - fixture

PATH = '/api/v1/identity/session'
GUARD = {'X-S21-Session': '1'}


@dataclass
class FakeProvider:
    key: rsa.RSAPrivateKey
    subject: str = 'target-subject'
    refreshed: list[str] = field(default_factory=list)
    logged_out: list[str] = field(default_factory=list)

    def refresh(self, refresh_token: str) -> RefreshedSession:
        self.refreshed.append(refresh_token)
        if refresh_token == 'vencida':
            raise SessionRefreshError('invalid')
        if refresh_token == 'fora-do-ar':
            raise SessionRefreshError('unavailable')
        return RefreshedSession(s21_token(self.key, subject=self.subject), f'nova-{len(self.refreshed)}', 900)

    def logout(self, access_token: str) -> None:
        self.logged_out.append(access_token)


@pytest.fixture
def session(s21: tuple[IdentityFixture, rsa.RSAPrivateKey, TestClient]) -> tuple[IdentityFixture, rsa.RSAPrivateKey, TestClient, FakeProvider]:  # noqa: F811
    identity, key, _ = s21  # noqa: F811
    app = identity.app
    app.state.settings = app.state.settings.model_copy(update={
        's21_login_url': HttpUrl(S21_URL), 's21_login_publishable_key': 'chave-publicavel-ficticia',
        's21_login_tenant_id': identity.tenant_a})
    provider = FakeProvider(key)
    app.state.s21_sessions = provider
    return identity, key, TestClient(app, base_url='https://testserver'), provider


def _handoff(client: TestClient, token: str, refresh_token: str = 'r1', headers: dict[str, str] | None = None):  # type: ignore[no-untyped-def]
    return client.post(PATH, json={'refresh_token': refresh_token}, headers={**_headers(token), **(headers or GUARD)})


def test_handoff_after_code_sets_httponly_cookie_and_returns_new_pass(session) -> None:  # type: ignore[no-untyped-def]
    _, key, client, provider = session
    response = _handoff(client, s21_token(key))
    assert response.status_code == 200, response.json()
    assert set(response.json()) == {'access_token', 'expires_in'} and provider.refreshed == ['r1']
    cookie = response.headers['set-cookie']
    for attribute in ('s21_contabil_session=nova-1', 'HttpOnly', 'Secure', 'SameSite=strict',
                      'Path=/api/v1/identity/session', 'Max-Age=1200'):
        assert attribute in cookie
    assert response.headers['cache-control'] == 'no-store'
    assert 'nova-1' not in response.text  # a renovação nunca volta para a página


def test_f5_refresh_uses_cookie_rotates_it_and_enters(session) -> None:  # type: ignore[no-untyped-def]
    _, key, client, provider = session
    _handoff(client, s21_token(key))
    response = client.post(PATH + '/refresh', headers=GUARD)
    assert response.status_code == 200 and provider.refreshed == ['r1', 'nova-1']
    assert 's21_contabil_session=nova-2' in response.headers['set-cookie']
    me = client.get('/api/v1/identity/me', headers=_headers(response.json()['access_token']))
    assert me.status_code == 200


def test_refresh_without_cookie_or_with_ended_session_clears_cookie(session) -> None:  # type: ignore[no-untyped-def]
    _, _, client, provider = session
    response = client.post(PATH + '/refresh', headers=GUARD)
    assert response.status_code == 401 and provider.refreshed == []
    client.cookies.set('s21_contabil_session', 'vencida')
    response = client.post(PATH + '/refresh', headers=GUARD)
    assert response.status_code == 401 and 'Max-Age=0' in response.headers['set-cookie']


def test_login_service_down_is_503_and_keeps_cookie(session) -> None:  # type: ignore[no-untyped-def]
    _, _, client, _ = session
    client.cookies.set('s21_contabil_session', 'fora-do-ar')
    response = client.post(PATH + '/refresh', headers=GUARD)
    assert response.status_code == 503 and 'set-cookie' not in response.headers


def test_session_routes_require_own_header(session) -> None:  # type: ignore[no-untyped-def]
    _, key, client, provider = session
    assert _handoff(client, s21_token(key), headers={'X-S21-Session': '0'}).status_code == 403
    assert client.post(PATH + '/refresh').status_code == 403
    assert client.post(PATH + '/logout').status_code == 403
    assert provider.refreshed == []


def test_handoff_refuses_missing_pass_bridge_pass_and_unregistered_person(session) -> None:  # type: ignore[no-untyped-def]
    identity, key, client, provider = session
    assert client.post(PATH, json={'refresh_token': 'r1'}, headers=GUARD).status_code == 401
    assert _handoff(client, s21_token(key, aal='aal1')).status_code == 401
    assert _handoff(client, s21_token(key, subject='sem-cadastro')).status_code == 403
    assert _handoff(client, identity.token()).status_code == 403  # passe da ponte não abre sessão de cookie
    assert provider.refreshed == []


def test_handoff_refuses_renewal_of_another_person(session) -> None:  # type: ignore[no-untyped-def]
    _, key, client, provider = session
    provider.subject = 'outra-pessoa'
    response = _handoff(client, s21_token(key))
    assert response.status_code == 401 and len(provider.logged_out) == 1
    assert 'Max-Age=0' in response.headers['set-cookie']


def test_logout_ends_supabase_session_and_clears_cookie(session) -> None:  # type: ignore[no-untyped-def]
    _, key, client, provider = session
    _handoff(client, s21_token(key))
    token = s21_token(key)
    response = client.post(PATH + '/logout', headers={**_headers(token), **GUARD})
    assert response.status_code == 200 and provider.logged_out == [token]
    assert 'Max-Age=0' in response.headers['set-cookie']
    assert client.post(PATH + '/refresh', headers=GUARD).status_code == 401


def test_without_s21_login_the_feature_is_off(session) -> None:  # type: ignore[no-untyped-def]
    identity, _, client, _ = session
    identity.app.state.s21_sessions = None
    assert client.post(PATH + '/refresh', headers=GUARD).status_code == 409
