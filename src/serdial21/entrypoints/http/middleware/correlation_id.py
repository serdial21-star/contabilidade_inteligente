'''Middleware ASGI para correlação segura de requisições HTTP.'''

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

from serdial21.shared_kernel.correlation import (
    correlation_id_context,
    request_id_context,
)


CORRELATION_ID_HEADER = b'x-correlation-id'
REQUEST_ID_HEADER = b'x-request-id'
ASGIReceiveCallable = Callable[[], Awaitable[dict[str, Any]]]
ASGISendCallable = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[
    [dict[str, Any], ASGIReceiveCallable, ASGISendCallable],
    Awaitable[None],
]


class CorrelationIdMiddleware:
    '''Propaga um UUID por requisição e o devolve no cabeçalho da resposta.'''

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: ASGIReceiveCallable,
        send: ASGISendCallable,
    ) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        headers = scope.get('headers', [])
        request_id = self._resolve_id(headers, REQUEST_ID_HEADER) or str(uuid4())
        correlation_id = (
            self._resolve_id(headers, CORRELATION_ID_HEADER) or request_id
        )
        scope.setdefault('state', {})['correlation_id'] = correlation_id
        scope['state']['request_id'] = request_id
        correlation_token = correlation_id_context.set(correlation_id)
        request_token = request_id_context.set(request_id)

        async def send_with_correlation(message: dict[str, Any]) -> None:
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                headers.append((CORRELATION_ID_HEADER, correlation_id.encode('ascii')))
                headers.append((REQUEST_ID_HEADER, request_id.encode('ascii')))
                message['headers'] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation)
        finally:
            request_id_context.reset(request_token)
            correlation_id_context.reset(correlation_token)

    @staticmethod
    def _resolve_id(
        headers: list[tuple[bytes, bytes]], header_name: bytes,
    ) -> str | None:
        for name, value in headers:
            if name.lower() != header_name:
                continue
            try:
                return str(UUID(value.decode('ascii')))
            except (UnicodeDecodeError, ValueError):
                break
        return None
