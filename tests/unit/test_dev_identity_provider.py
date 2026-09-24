'''Provedor OIDC de desenvolvimento (scripts/dev_identity_provider.py): regra crítica é
recusar rodar fora de development/test, e a chave deve ser estável entre chamadas.'''

import importlib.util
from pathlib import Path

import jwt
from jwt.algorithms import RSAAlgorithm
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts' / 'dev_identity_provider.py'


def _load_module():
    spec = importlib.util.spec_from_file_location('dev_identity_provider', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def provider(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, 'KEY_DIR', tmp_path)
    monkeypatch.setattr(module, 'PRIVATE_KEY_PATH', tmp_path / 'private_key.pem')
    return module


class _FakeSettings:
    def __init__(self, environment: str) -> None:
        self.environment = environment


@pytest.mark.parametrize('environment', ['development', 'test'])
def test_dev_environments_are_accepted(provider, environment) -> None:
    provider.require_dev_environment(_FakeSettings(environment))  # não deve lançar


@pytest.mark.parametrize('environment', ['homologation', 'production'])
def test_secured_environments_are_refused(provider, environment) -> None:
    with pytest.raises(provider.DevOnlyEnvironmentError):
        provider.require_dev_environment(_FakeSettings(environment))


def test_key_is_generated_once_and_reused(provider) -> None:
    first = provider.load_or_create_private_key()
    first_pem = first.private_bytes(
        encoding=provider.serialization.Encoding.PEM,
        format=provider.serialization.PrivateFormat.PKCS8,
        encryption_algorithm=provider.serialization.NoEncryption(),
    )
    second = provider.load_or_create_private_key()
    second_pem = second.private_bytes(
        encoding=provider.serialization.Encoding.PEM,
        format=provider.serialization.PrivateFormat.PKCS8,
        encryption_algorithm=provider.serialization.NoEncryption(),
    )
    assert first_pem == second_pem  # segunda chamada carrega, não gera outra chave


def test_jwks_key_matches_signing_key_and_token_verifies(provider) -> None:
    key = provider.load_or_create_private_key()
    jwks = provider.build_jwks(key.public_key())
    assert jwks['keys'][0]['kid'] == provider.KID
    assert jwks['keys'][0]['alg'] == 'RS256'

    token = jwt.encode(
        {'iss': 'http://127.0.0.1:8090', 'aud': 'serdial21-dev-api', 'sub': 'dev-sergio',
         'tenant_id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'iat': 0, 'exp': 9_999_999_999},
        key, algorithm='RS256', headers={'kid': provider.KID},
    )
    public_key = RSAAlgorithm.from_jwk(jwks['keys'][0])
    claims = jwt.decode(
        token, public_key, algorithms=['RS256'], audience='serdial21-dev-api',
        issuer='http://127.0.0.1:8090',
    )
    assert claims['sub'] == 'dev-sergio'


def test_jwks_from_a_different_key_does_not_verify(provider) -> None:
    key = provider.load_or_create_private_key()
    other_key = provider.rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        {'iss': 'http://127.0.0.1:8090', 'aud': 'serdial21-dev-api', 'sub': 'dev-sergio',
         'tenant_id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'iat': 0, 'exp': 9_999_999_999},
        other_key, algorithm='RS256', headers={'kid': provider.KID},
    )
    jwks_for_first_key = provider.build_jwks(key.public_key())
    public_key = RSAAlgorithm.from_jwk(jwks_for_first_key['keys'][0])
    with pytest.raises(jwt.exceptions.InvalidSignatureError):
        jwt.decode(token, public_key, algorithms=['RS256'], audience='serdial21-dev-api',
                   issuer='http://127.0.0.1:8090')
