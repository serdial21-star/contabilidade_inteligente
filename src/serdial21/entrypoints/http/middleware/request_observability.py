'''Observa requests HTTP sem registrar cabeçalhos, query ou corpo.'''

from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

from serdial21.shared_kernel.observability import MetricsRegistry, sanitized_error, technical_event


ASGIReceiveCallable = Callable[[], Awaitable[dict[str, Any]]]
ASGISendCallable = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[dict[str, Any], ASGIReceiveCallable, ASGISendCallable], Awaitable[None]]


class RequestObservabilityMiddleware:
    def __init__(self, app: ASGIApp, *, metrics: MetricsRegistry) -> None:
        self.app = app
        self._metrics = metrics

    async def __call__(self, scope: dict[str, Any], receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        started = perf_counter()
        status_code = 500
        error_type: str | None = None

        async def send_with_status(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = int(message['status'])
            await send(message)

        try:
            await self.app(scope, receive, send_with_status)
        except Exception as error:
            error_type = sanitized_error(error)
            raise
        finally:
            duration = perf_counter() - started
            self._metrics.observe_processing(duration)
            if status_code >= 500 or error_type is not None:
                self._metrics.increment('errors_total')
            fields: dict[str, object] = {
                'method': scope.get('method', 'UNKNOWN'),
                'path': scope.get('path', ''),
                'status': status_code,
                'duration_ms': round(duration * 1000, 3),
            }
            if error_type is not None:
                fields['error_type'] = error_type
            technical_event('http.request.completed', fields=fields)
