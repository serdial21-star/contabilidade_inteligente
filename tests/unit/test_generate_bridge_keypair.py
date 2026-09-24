'''scripts/generate_bridge_keypair.py: nunca sobrescrever uma chave já existente.'''

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts' / 'generate_bridge_keypair.py'


def _load_module():
    spec = importlib.util.spec_from_file_location('generate_bridge_keypair', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def script(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, 'OUTPUT_DIR', tmp_path)
    monkeypatch.setattr(module, 'PRIVATE_KEY_PATH', tmp_path / 'private_key.pem')
    return module


def test_first_run_creates_a_valid_key_and_matching_jwk(script) -> None:
    from cryptography.hazmat.primitives import serialization
    import jwt
    from jwt.algorithms import RSAAlgorithm

    assert script.main() == 0
    assert script.PRIVATE_KEY_PATH.is_file()
    private_key = serialization.load_pem_private_key(
        script.PRIVATE_KEY_PATH.read_bytes(), password=None,
    )
    jwk = json_loads_public_jwk(script, private_key.public_key())
    token = jwt.encode({'a': 1}, private_key, algorithm='RS256', headers={'kid': script.KID})
    jwt.decode(token, RSAAlgorithm.from_jwk(jwk), algorithms=['RS256'])  # não lança


def json_loads_public_jwk(script, public_key):
    import json
    from jwt.algorithms import RSAAlgorithm
    jwk = json.loads(RSAAlgorithm.to_jwk(public_key))
    jwk.update({'kid': script.KID, 'use': 'sig', 'alg': 'RS256'})
    return jwk


def test_second_run_refuses_to_overwrite_the_existing_key(script) -> None:
    assert script.main() == 0
    original = script.PRIVATE_KEY_PATH.read_bytes()
    assert script.main() == 1  # recusa: já existe
    assert script.PRIVATE_KEY_PATH.read_bytes() == original
