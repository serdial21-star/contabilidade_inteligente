'''Contrato de rate limit e backend local determinístico por janela fixa.'''

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from hashlib import sha256
import json
from threading import Lock
from time import monotonic
from typing import Any, Protocol

from serdial21.shared_kernel.observability import MetricsRegistry, security_event


ASGIMessage = dict[str, Any]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIApp = Callable[[dict[str, Any], ASGIReceive, ASGISend], Awaitable[None]]


class RateLimiter(Protocol):
    async def allow(
        self, identity: str, bucket: str, limit: int, window_seconds: int,
    ) -> bool: ...

    async def aclose(self) -> None: ...


class RateLimiterUnavailable(RuntimeError):
    '''Backend distribuído indisponível; nunca libera tráfego por fallback.'''


@dataclass
class _Window:
    started_at: float
    count: int


class InMemoryRateLimiter:
    '''Adequado somente a local/test; não coordena múltiplas instâncias.'''

    def __init__(
        self, *, clock: Callable[[], float] = monotonic, max_keys: int = 10_000,
    ) -> None:
        if max_keys < 1:
            raise ValueError('max_keys must be positive')
        self._clock = clock
        self._max_keys = max_keys
        self._windows: dict[tuple[str, str], _Window] = {}
        self._lock = Lock()

    async def allow(
        self, identity: str, bucket: str, limit: int, window_seconds: int,
    ) -> bool:
        now = self._clock()
        key = (identity, bucket)
        with self._lock:
            window = self._windows.get(key)
            if window is None and len(self._windows) >= self._max_keys:
                self._windows = {
                    item_key: item
                    for item_key, item in self._windows.items()
                    if now - item.started_at < window_seconds
                }
                if len(self._windows) >= self._max_keys:
                    return False
            if window is None or now - window.started_at >= window_seconds:
                self._windows[key] = _Window(now, 1)
                return True
            if window.count >= limit:
                return False
            window.count += 1
            return True

    async def aclose(self) -> None:
        return None


class RateLimitMiddleware:
    def __init__(
        self, app: ASGIApp, *, limiter: RateLimiter,
        general_limit: int, sensitive_limit: int, upload_limit: int,
        metrics: MetricsRegistry,
    ) -> None:
        self.app = app
        self._limiter = limiter
        self._limits = {
            'general': general_limit,
            'sensitive': sensitive_limit,
            'upload': upload_limit,
        }
        self._metrics = metrics

    async def __call__(
        self, scope: dict[str, Any], receive: ASGIReceive, send: ASGISend,
    ) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        bucket = _bucket(str(scope.get('path', '')), str(scope.get('method', 'GET')))
        identity = _safe_identity(scope)
        try:
            allowed = await self._limiter.allow(
                identity, bucket, self._limits[bucket], 60,
            )
        except RateLimiterUnavailable:
            self._metrics.increment(
                'rate_limit_backend_unavailable_total', {'bucket': bucket},
            )
            security_event('rate_limit.backend_unavailable', fields={'bucket': bucket})
            body = json.dumps(
                {'detail': 'service temporarily unavailable'}, separators=(',', ':'),
            ).encode()
            await send({
                'type': 'http.response.start', 'status': 503,
                'headers': [
                    (b'content-type', b'application/json'),
                    (b'content-length', str(len(body)).encode()),
                    (b'retry-after', b'5'),
                ],
            })
            await send({'type': 'http.response.body', 'body': body})
            return
        if not allowed:
            self._metrics.increment('rate_limit_exceeded_total', {'bucket': bucket})
            security_event('rate_limit.exceeded', fields={'bucket': bucket})
            body = json.dumps({'detail': 'rate limit exceeded'}, separators=(',', ':')).encode()
            await send({
                'type': 'http.response.start', 'status': 429,
                'headers': [
                    (b'content-type', b'application/json'),
                    (b'content-length', str(len(body)).encode()),
                    (b'retry-after', b'60'),
                ],
            })
            await send({'type': 'http.response.body', 'body': body})
            return
        await self.app(scope, receive, send)


def _bucket(path: str, method: str) -> str:
    if method == 'POST' and ('/imports/nfe' in path or '/imports/ofx' in path):
        return 'upload'
    if '/identity/' in path or (
        method == 'POST' and (path.endswith('/approve') or path.endswith('/reject'))
    ):
        return 'sensitive'
    return 'general'


def _safe_identity(scope: dict[str, Any]) -> str:
    headers = {name.lower(): value for name, value in scope.get('headers', [])}
    authorization = headers.get(b'authorization')
    if authorization:
        return f'bearer:{sha256(authorization).hexdigest()}'
    client = scope.get('client')
    host = str(client[0]) if client else 'unknown'
    return f'client:{host}'
