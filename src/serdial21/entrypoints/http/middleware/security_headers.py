'''Cabeçalhos defensivos aplicados a toda resposta HTTP da API.'''

from collections.abc import Awaitable, Callable
from typing import Any


ASGIReceiveCallable = Callable[[], Awaitable[dict[str, Any]]]
ASGISendCallable = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[
    [dict[str, Any], ASGIReceiveCallable, ASGISendCallable],
    Awaitable[None],
]


SECURITY_HEADERS: tuple[tuple[bytes, bytes], ...] = (
    (b'cache-control', b'no-store'),
    (b'content-security-policy', b"default-src 'none'; base-uri 'none'; frame-ancestors 'none'"),
    (b'permissions-policy', b'camera=(), geolocation=(), microphone=()'),
    (b'referrer-policy', b'no-referrer'),
    (b'x-content-type-options', b'nosniff'),
    (b'x-frame-options', b'DENY'),
)


class SecurityHeadersMiddleware:
    '''Evita que respostas da API sejam interpretadas ou embutidas indevidamente.'''

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

        async def send_with_security_headers(message: dict[str, Any]) -> None:
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                existing = {name.lower() for name, _ in headers}
                headers.extend(
                    (name, value)
                    for name, value in SECURITY_HEADERS
                    if name not in existing
                )
                message['headers'] = headers
            await send(message)

        await self.app(scope, receive, send_with_security_headers)
