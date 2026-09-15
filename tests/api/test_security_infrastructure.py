import asyncio

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from serdial21.bootstrap.application import create_app
from serdial21.bootstrap.settings import AppSettings
from serdial21.entrypoints.http.middleware.rate_limit import InMemoryRateLimiter


def _production_settings(**overrides: object) -> AppSettings:
    values: dict[str, object] = {
        '_env_file': None,
        'environment': 'production',
        'database_url': 'mysql+pymysql://user:placeholder@db.example.test/serdial21',
        'oidc_issuer': 'https://id.example.test',
        'oidc_audience': 'serdial21-api',
        'oidc_jwks_url': 'https://id.example.test/jwks.json',
        'public_frontend_url': 'https://app.example.test',
        'cors_allowed_origins': 'https://app.example.test',
        'trusted_hosts': 'api.example.test,testserver',
        'external_https': True,
        'rate_limit_backend': 'distributed',
        'rate_limit_backend_url': 'rediss://rate-limit.example.test/0',
    }
    values.update(overrides)
    return AppSettings(**values)


@pytest.mark.parametrize('field,value,expected', [
    ('cors_allowed_origins', '', 'CORS_ALLOWED_ORIGINS'),
    ('trusted_hosts', '', 'TRUSTED_HOSTS'),
    ('public_frontend_url', None, 'PUBLIC_FRONTEND_URL'),
    ('external_https', False, 'EXTERNAL_HTTPS'),
    ('rate_limit_backend', 'memory', 'rate limit distribuído'),
])
def test_production_security_configuration_fails_closed(
    field: str, value: object, expected: str,
) -> None:
    with pytest.raises(ValidationError, match=expected):
        _production_settings(**{field: value})


def test_production_rejects_wildcards_local_origins_and_malformed_origins() -> None:
    with pytest.raises(ValidationError, match='wildcard'):
        _production_settings(trusted_hosts='*')
    with pytest.raises(ValidationError, match='HTTPS público'):
        _production_settings(
            public_frontend_url='https://app.example.test',
            cors_allowed_origins='http://localhost:8080,https://app.example.test',
        )
    with pytest.raises(ValidationError, match='origem inválida'):
        AppSettings(_env_file=None, cors_allowed_origins='https://example.test/path')
    with pytest.raises(ValidationError, match='host inválido'):
        _production_settings(trusted_hosts='https://api.example.test')
    with pytest.raises(ValidationError, match='usar TLS'):
        _production_settings(rate_limit_backend_url='redis://rate-limit.example.test/0')


def test_distributed_rate_limit_configuration_requires_injected_adapter() -> None:
    with pytest.raises(ValueError, match='distributed rate limiter adapter'):
        create_app(_production_settings())


def test_cors_preflight_allowlist_and_unknown_origin() -> None:
    settings = AppSettings(
        _env_file=None, environment='test',
        cors_allowed_origins='https://app.example.test',
        trusted_hosts='testserver',
    )
    client = TestClient(create_app(settings))
    headers = {
        'Origin': 'https://app.example.test',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Authorization,X-Correlation-ID',
    }
    allowed = client.options('/api/v1/health/live', headers=headers)
    denied = client.options(
        '/api/v1/health/live',
        headers=headers | {'Origin': 'https://unknown.example.test'},
    )
    assert allowed.status_code == 200
    assert allowed.headers['access-control-allow-origin'] == 'https://app.example.test'
    assert 'authorization' in allowed.headers['access-control-allow-headers'].lower()
    assert denied.status_code == 400
    assert 'access-control-allow-origin' not in denied.headers


def test_trusted_host_security_headers_hsts_docs_and_safe_error() -> None:
    app = create_app(_production_settings(), rate_limiter=InMemoryRateLimiter())

    @app.get('/explode')
    def explode() -> None:
        raise RuntimeError('database path and secret must not escape')

    client = TestClient(app, raise_server_exceptions=False)
    bad_host = client.get('/api/v1/health/live', headers={'Host': 'evil.example.test'})
    response = client.get('/api/v1/health/live', headers={'Host': 'api.example.test'})
    failure = client.get('/explode', headers={'Host': 'api.example.test'})
    assert bad_host.status_code == 400
    assert response.status_code == 200
    assert response.headers['strict-transport-security'] == (
        'max-age=31536000; includeSubDomains'
    )
    assert response.headers['cache-control'] == 'no-store'
    assert client.get('/docs', headers={'Host': 'api.example.test'}).status_code == 404
    assert failure.status_code == 500
    assert failure.json() == {'detail': 'internal server error'}
    assert 'secret' not in failure.text and 'database' not in failure.text


def test_request_body_limits_are_route_specific() -> None:
    settings = AppSettings(
        _env_file=None, environment='test', general_request_max_bytes=1024,
        nfe_max_xml_bytes=2048, ofx_max_upload_bytes=4096,
    )
    client = TestClient(create_app(settings))
    general = client.post('/api/v1/unknown', content=b'x' * 1025)
    nfe = client.post(
        f'/api/v1/operations/companies/00000000-0000-0000-0000-000000000001/imports/nfe',
        content=b'x' * 2049,
    )
    ofx = client.post(
        f'/api/v1/operations/companies/00000000-0000-0000-0000-000000000001/imports/ofx',
        content=b'x' * 4097,
    )
    assert general.status_code == nfe.status_code == ofx.status_code == 413
    assert all(item.json() == {'detail': 'request body too large'} for item in (general, nfe, ofx))


def test_rate_limit_is_deterministic_separates_identities_and_resets() -> None:
    now = [0.0]
    limiter = InMemoryRateLimiter(clock=lambda: now[0])
    allow = lambda identity: asyncio.run(limiter.allow(identity, 'general', 2, 60))
    assert allow('a')
    assert allow('a')
    assert not allow('a')
    assert allow('b')
    now[0] = 60.0
    assert allow('a')

    bounded = InMemoryRateLimiter(clock=lambda: 0.0, max_keys=1)
    assert asyncio.run(bounded.allow('a', 'general', 1, 60))
    assert not asyncio.run(bounded.allow('b', 'general', 1, 60))


def test_http_rate_limit_returns_safe_429_and_hashes_bearer_identity() -> None:
    settings = AppSettings(
        _env_file=None, environment='test', rate_limit_general_per_minute=10,
    )
    client = TestClient(create_app(settings))
    headers = {'Authorization': 'Bearer synthetic-a'}
    responses = [client.get('/api/v1/health/live', headers=headers) for _ in range(11)]
    separate = client.get(
        '/api/v1/health/live', headers={'Authorization': 'Bearer synthetic-b'},
    )
    assert all(response.status_code == 200 for response in responses[:10])
    assert responses[-1].status_code == 429
    assert responses[-1].json() == {'detail': 'rate limit exceeded'}
    assert responses[-1].headers['retry-after'] == '60'
    assert separate.status_code == 200
