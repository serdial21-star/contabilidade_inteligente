from uuid import uuid4

from fastapi.testclient import TestClient

from serdial21.bootstrap.application import create_app
from serdial21.bootstrap.settings import AppSettings


TOKEN = 'synthetic-metrics-token-at-least-32-characters'


def build_app(**overrides: object):
    return create_app(AppSettings(
        _env_file=None,
        environment='test',
        metrics_endpoint_enabled=True,
        metrics_access_token=TOKEN,
        **overrides,
    ))


def test_request_and_correlation_ids_are_distinct_and_validated() -> None:
    request_id = str(uuid4())
    correlation_id = str(uuid4())
    response = TestClient(build_app()).get(
        '/api/v1/health/live',
        headers={
            'X-Request-ID': request_id,
            'X-Correlation-ID': correlation_id,
        },
    )

    assert response.headers['x-request-id'] == request_id
    assert response.headers['x-correlation-id'] == correlation_id


def test_invalid_request_id_is_replaced_without_reusing_attacker_value() -> None:
    response = TestClient(build_app()).get(
        '/api/v1/health/live', headers={'X-Request-ID': 'unsafe-value'}
    )

    assert response.headers['x-request-id'] != 'unsafe-value'
    assert response.headers['x-correlation-id'] == response.headers['x-request-id']


def test_metrics_endpoint_is_disabled_or_hidden_without_valid_secret() -> None:
    disabled = create_app(AppSettings(_env_file=None, environment='test'))
    assert TestClient(disabled).get('/internal/metrics').status_code == 404

    client = TestClient(build_app())
    assert client.get('/internal/metrics').status_code == 404
    assert client.get(
        '/internal/metrics', headers={'Authorization': 'Bearer wrong'}
    ).status_code == 404


def test_http_metrics_use_route_template_and_low_cardinality_labels() -> None:
    app = build_app()
    client = TestClient(app)
    untrusted_id = str(uuid4())
    client.get(f'/missing/{untrusted_id}')
    client.get('/api/v1/health/live')

    response = client.get(
        '/internal/metrics', headers={'Authorization': f'Bearer {TOKEN}'}
    )

    assert response.status_code == 200
    assert 'route_template="/health/live"' in response.text
    assert 'route_template="<unmatched>"' in response.text
    assert untrusted_id not in response.text
    assert TOKEN not in response.text
    assert 'tenant_id' not in response.text
    assert 'company_id' not in response.text


def test_payload_rejection_increments_security_metric() -> None:
    app = build_app(general_request_max_bytes=1024)
    client = TestClient(app)
    response = client.post('/missing', content=b'x' * 1025)

    assert response.status_code == 413
    metrics = app.state.metrics.render_prometheus()
    assert 'payload_too_large_total{source="general"} 1' in metrics
