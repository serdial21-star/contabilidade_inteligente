import asyncio
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from serdial21.bootstrap.application import create_app
from serdial21.bootstrap.settings import AppSettings


async def request(method: str, path: str) -> int:
    app = create_app(AppSettings(_env_file=None, environment='test'))
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url='http://testserver',
    ) as client:
        response = await client.request(method, path, json={'action': 'changed'})
    return response.status_code


def test_audit_event_has_no_common_edit_or_delete_api() -> None:
    path = f'/api/v1/audit/events/{uuid4()}'

    assert asyncio.run(request('PUT', path)) == 404
    assert asyncio.run(request('PATCH', path)) == 404
    assert asyncio.run(request('DELETE', path)) == 404
