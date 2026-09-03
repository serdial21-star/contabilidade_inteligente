'''Middleware ASGI para correlação segura de requisições HTTP.'''

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

from serdial21.shared_kernel.correlation import correlation_id_context


CORRELATION_ID_HEADER = b'x-correlation-id'
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

        correlation_id = self._resolve_correlation_id(scope.get('headers', []))
        scope.setdefault('state', {})['correlation_id'] = correlation_id
        token = correlation_id_context.set(correlation_id)

        async def send_with_correlation(message: dict[str, Any]) -> None:
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                headers.append((CORRELATION_ID_HEADER, correlation_id.encode('ascii')))
                message['headers'] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation)
        finally:
            correlation_id_context.reset(token)

    @staticmethod
    def _resolve_correlation_id(headers: list[tuple[bytes, bytes]]) -> str:
        for name, value in headers:
            if name.lower() != CORRELATION_ID_HEADER:
                continue
            try:
                return str(UUID(value.decode('ascii')))
            except (UnicodeDecodeError, ValueError):
                break
        return str(uuid4())
