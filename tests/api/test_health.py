import asyncio
from uuid import UUID, uuid4

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from serdial21 import __version__
from serdial21.bootstrap.application import create_app
from serdial21.bootstrap.settings import AppSettings


def build_app() -> FastAPI:
    settings = AppSettings(_env_file=None, environment='test')
    return create_app(settings)


async def async_get(
    app: FastAPI,
    path: str,
    headers: dict[str, str] | None = None,
) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url='http://testserver',
    ) as client:
        return await client.get(path, headers=headers)


def test_liveness_contract() -> None:
    response = asyncio.run(async_get(build_app(), '/api/v1/health/live'))

    assert response.status_code == 200
    assert response.json() == {
        'status': 'ok',
        'service': 'Serdial21 Contabilidade Inteligente',
        'environment': 'test',
        'version': __version__,
    }
    UUID(response.headers['x-correlation-id'])


def test_valid_correlation_id_is_propagated() -> None:
    correlation_id = str(uuid4())

    response = asyncio.run(
        async_get(
            build_app(),
            '/api/v1/health/live',
            headers={'X-Correlation-ID': correlation_id},
        )
    )

    assert response.headers['x-correlation-id'] == correlation_id


def test_invalid_correlation_id_is_replaced() -> None:
    response = asyncio.run(
        async_get(
            build_app(),
            '/api/v1/health/live',
            headers={'X-Correlation-ID': 'not-a-uuid'},
        )
    )

    generated_id = response.headers['x-correlation-id']
    assert generated_id != 'not-a-uuid'
    UUID(generated_id)


def test_custom_api_prefix_is_used() -> None:
    settings = AppSettings(_env_file=None, environment='test', api_prefix='/internal')
    app = create_app(settings)

    response = asyncio.run(async_get(app, '/internal/health/live'))

    assert response.status_code == 200


def test_readiness_is_unavailable_without_database_configuration() -> None:
    response = asyncio.run(async_get(build_app(), '/api/v1/health/ready'))

    assert response.status_code == 503
    assert response.json() == {
        'status': 'unavailable',
        'service': 'database',
    }


def test_readiness_validates_database_connection() -> None:
    settings = AppSettings(
        _env_file=None,
        environment='test',
        database_url='sqlite+pysqlite:///:memory:',
    )
    app = create_app(settings)

    response = asyncio.run(async_get(app, '/api/v1/health/ready'))
    app.state.database.dispose()

    assert response.status_code == 200
    assert response.json() == {'status': 'ok', 'service': 'database'}
