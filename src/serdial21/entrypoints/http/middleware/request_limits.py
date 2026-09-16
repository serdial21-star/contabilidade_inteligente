'''Limites de corpo aplicados antes de parsing, autenticação e casos de uso.'''

from collections.abc import Awaitable, Callable
import json
from typing import Any

from serdial21.shared_kernel.observability import MetricsRegistry, security_event


ASGIMessage = dict[str, Any]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIApp = Callable[[dict[str, Any], ASGIReceive, ASGISend], Awaitable[None]]


class RequestBodyTooLargeError(RuntimeError):
    pass


class RequestBodyLimitMiddleware:
    def __init__(
        self, app: ASGIApp, *, api_prefix: str, general_limit: int,
        nfe_limit: int, ofx_limit: int, metrics: MetricsRegistry,
    ) -> None:
        self.app = app
        self._nfe_path = f'{api_prefix}/operations/companies/'
        self._general_limit = general_limit
        self._nfe_limit = nfe_limit
        self._ofx_limit = ofx_limit
        self._metrics = metrics

    async def __call__(
        self, scope: dict[str, Any], receive: ASGIReceive, send: ASGISend,
    ) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        limit = self._limit_for(str(scope.get('path', '')))
        headers = {name.lower(): value for name, value in scope.get('headers', [])}
        raw_length = headers.get(b'content-length')
        if raw_length is not None:
            try:
                content_length = int(raw_length)
            except ValueError:
                await _json_response(send, 400, 'invalid content length')
                return
            if content_length < 0:
                await _json_response(send, 400, 'invalid content length')
                return
            if content_length > limit:
                self._record_rejection(str(scope.get('path', '')))
                await _json_response(send, 413, 'request body too large')
                return

        consumed = 0
        response_started = False

        async def limited_receive() -> ASGIMessage:
            nonlocal consumed
            message = await receive()
            if message['type'] == 'http.request':
                consumed += len(message.get('body', b''))
                if consumed > limit:
                    raise RequestBodyTooLargeError()
            return message

        async def tracked_send(message: ASGIMessage) -> None:
            nonlocal response_started
            if message['type'] == 'http.response.start':
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except RequestBodyTooLargeError:
            if response_started:
                raise
            self._record_rejection(str(scope.get('path', '')))
            await _json_response(send, 413, 'request body too large')

    def _record_rejection(self, path: str) -> None:
        source = 'nfe' if path.endswith('/imports/nfe') else (
            'ofx' if path.endswith('/imports/ofx') else 'general'
        )
        self._metrics.increment('payload_too_large_total', {'source': source})
        security_event('payload.rejected', fields={'reason': 'too_large', 'source': source})

    def _limit_for(self, path: str) -> int:
        if path.startswith(self._nfe_path) and path.endswith('/imports/nfe'):
            return self._nfe_limit
        if path.startswith(self._nfe_path) and path.endswith('/imports/ofx'):
            return self._ofx_limit
        return self._general_limit


async def _json_response(send: ASGISend, status: int, detail: str) -> None:
    body = json.dumps({'detail': detail}, separators=(',', ':')).encode()
    await send({
        'type': 'http.response.start', 'status': status,
        'headers': [
            (b'content-type', b'application/json'),
            (b'content-length', str(len(body)).encode()),
        ],
    })
    await send({'type': 'http.response.body', 'body': body})
