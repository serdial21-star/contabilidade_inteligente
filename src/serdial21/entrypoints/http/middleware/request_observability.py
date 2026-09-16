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
            route = scope.get('route')
            route_template = str(getattr(route, 'path', '<unmatched>'))
            method = str(scope.get('method', 'UNKNOWN'))
            self._metrics.record_http(
                method=method,
                route_template=route_template,
                status_code=status_code,
                duration_seconds=duration,
            )
            if status_code == 401:
                self._metrics.increment('auth_failures_total', {'reason': 'http_401'})
            elif status_code == 403:
                self._metrics.increment(
                    'authorization_denials_total', {'reason': 'http_403'}
                )
            elif status_code == 423:
                self._metrics.increment('account_lock_block_total')
            elif status_code == 422 and route_template.endswith('/imports/nfe'):
                self._metrics.increment('parser_rejection_total', {'source': 'nfe'})
            elif status_code == 422 and route_template.endswith('/imports/ofx'):
                self._metrics.increment('parser_rejection_total', {'source': 'ofx'})
            if status_code >= 500 or error_type is not None:
                self._metrics.increment('errors_total')
            fields: dict[str, object] = {
                'method': method,
                'route': route_template,
                'status_code': status_code,
                'duration_ms': round(duration * 1000, 3),
            }
            if error_type is not None:
                fields['error_type'] = error_type
            technical_event('http.request.completed', fields=fields)
