'''T-0012 (ADR 0025 do Sistema C): o S21 Contábil aceita o login único S21 ao lado da ponte do Sistema A.

O passe S21 (Supabase do Financeiro) não traz tenant_id: o escritório vem da configuração do servidor. Só vale com
role "authenticated", não anônimo e com o código do celular (aal2); e o usuário continua precisando de cadastro no B.
'''
from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import update

from serdial21.bootstrap.database import session_scope
from serdial21.bootstrap.identity import build_oidc_verifier
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import UserModel
from serdial21.modules.identity.adapters.inbound.oidc import (
    IssuerRoutingVerifier,
    OidcJwtVerifier,
    s21_login_claims_acceptable,
)
from tests.api.test_identity_security import (  # noqa: F401 - fixture
    AUDIENCE,
    ISSUER,
    NOW,
    IdentityFixture,
    _headers,
    _onboard,
    identity,
)

S21_URL = 'https://s21-login.example.test'
S21_ISSUER = S21_URL + '/auth/v1'


def s21_token(key: rsa.RSAPrivateKey, subject: str = 'target-subject', **changes: Any) -> str:
    claims: dict[str, Any] = {
        'iss': S21_ISSUER, 'sub': subject, 'aud': 'authenticated', 'role': 'authenticated', 'aal': 'aal2',
        'is_anonymous': False, 'iat': int((NOW - timedelta(minutes=1)).timestamp()),
        'exp': int((NOW + timedelta(minutes=10)).timestamp()),
    }
    claims.update(changes)
    return jwt.encode({name: value for name, value in claims.items() if value is not None}, key, algorithm='RS256',
                      headers={'kid': 's21-key'})


@pytest.fixture
def s21(identity: IdentityFixture) -> tuple[IdentityFixture, rsa.RSAPrivateKey, TestClient]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    bridge = identity.app.state.oidc_verifier
    s21_verifier = OidcJwtVerifier(
        issuer=S21_ISSUER, audience='authenticated', jwks_url=S21_ISSUER + '/.well-known/jwks.json', leeway_seconds=0,
        signing_key_resolver=lambda _: key.public_key(), fixed_tenant_id=identity.tenant_a,
        claims_check=s21_login_claims_acceptable,
    )
    identity.app.state.oidc_verifier = IssuerRoutingVerifier({ISSUER: bridge, S21_ISSUER: s21_verifier})
    client = TestClient(identity.app)
    target_user_id, _ = _onboard(client, identity)
    # Como o comando de cadastro faz com --issuer do login S21: o mesmo usuário passa a ser do emissor S21.
    assert identity.app.state.database.session_factory is not None
    with session_scope(identity.app.state.database.session_factory) as session:
        session.execute(update(UserModel).where(UserModel.id == target_user_id).values(provider_issuer=S21_ISSUER))
    return identity, key, client


def test_s21_token_with_code_and_registration_enters(s21: tuple[IdentityFixture, rsa.RSAPrivateKey, TestClient]) -> None:
    identity, key, client = s21
    response = client.get('/api/v1/identity/me', headers=_headers(s21_token(key)))
    assert response.status_code == 200, response.json()
    assert response.json()['tenant']['id'] == str(identity.tenant_a)


@pytest.mark.parametrize('changes', [
    {'aal': 'aal1'},  # sem o código do celular
    {'aal': None},
    {'is_anonymous': True},
    {'role': 'anon'},
    {'aud': 'outra-audiencia'},
    {'iss': 'https://outro-emissor.example.test/auth/v1'},
    {'exp': int((NOW - timedelta(minutes=1)).timestamp())},
])
def test_s21_token_rules_are_enforced(s21: tuple[IdentityFixture, rsa.RSAPrivateKey, TestClient], changes: dict[str, Any]) -> None:
    _, key, client = s21
    response = client.get('/api/v1/identity/me', headers=_headers(s21_token(key, **changes)))
    assert response.status_code == 401
    assert response.json() == {'detail': 'authentication failed'}


def test_s21_token_signed_by_other_key_is_rejected(s21: tuple[IdentityFixture, rsa.RSAPrivateKey, TestClient]) -> None:
    _, _, client = s21
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert client.get('/api/v1/identity/me', headers=_headers(s21_token(other))).status_code == 401


def test_s21_token_without_registration_in_b_is_denied(s21: tuple[IdentityFixture, rsa.RSAPrivateKey, TestClient]) -> None:
    _, key, client = s21
    response = client.get('/api/v1/identity/me', headers=_headers(s21_token(key, subject='sem-cadastro')))
    assert response.status_code == 403 and response.json() == {'detail': 'access denied'}


def test_bridge_keeps_working_during_transition(s21: tuple[IdentityFixture, rsa.RSAPrivateKey, TestClient]) -> None:
    identity, _, client = s21
    assert client.get('/api/v1/identity/me', headers=_headers(identity.token())).status_code == 200


def test_s21_claims_rule() -> None:
    assert s21_login_claims_acceptable({'role': 'authenticated', 'aal': 'aal2', 'is_anonymous': False})
    assert not s21_login_claims_acceptable({'role': 'authenticated', 'aal': 'aal1'})
    assert not s21_login_claims_acceptable({'role': 'authenticated', 'aal': 'aal2', 'is_anonymous': True})
    assert not s21_login_claims_acceptable({'role': 'service_role', 'aal': 'aal2'})


def test_settings_build_routing_and_public_login_config() -> None:
    tenant = UUID('5463ce7c-31b5-471d-97aa-89f043292ebb')
    settings = AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:',
                           oidc_issuer=ISSUER, oidc_audience=AUDIENCE, oidc_jwks_url=f'{ISSUER}/jwks.json',
                           s21_login_url=S21_URL, s21_login_publishable_key='chave-publicavel-ficticia',
                           s21_login_tenant_id=tenant)
    assert isinstance(build_oidc_verifier(settings), IssuerRoutingVerifier)
    assert settings.s21_login_issuer == S21_ISSUER
    only_bridge = AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:',
                              oidc_issuer=ISSUER, oidc_audience=AUDIENCE, oidc_jwks_url=f'{ISSUER}/jwks.json')
    assert isinstance(build_oidc_verifier(only_bridge), OidcJwtVerifier)
    with pytest.raises(ValueError, match='S21_LOGIN'):
        AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:', s21_login_url=S21_URL)

    from serdial21.bootstrap.application import create_app
    client = TestClient(create_app(settings))
    assert client.get('/api/v1/identity/login-config').json() == {
        's21': {'url': S21_URL, 'publishable_key': 'chave-publicavel-ficticia'}}
    client = TestClient(create_app(only_bridge))
    assert client.get('/api/v1/identity/login-config').json() == {'s21': None}
