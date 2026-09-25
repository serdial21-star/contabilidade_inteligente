'''Adaptador Redis assíncrono para rate limit distribuído por janela fixa.'''

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from serdial21.entrypoints.http.middleware.rate_limit import RateLimiterUnavailable


_ALLOW_SCRIPT = '''
local count = redis.call('INCR', KEYS[1])
if count == 1 or redis.call('TTL', KEYS[1]) < 0 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
'''


class AsyncRedisClient(Protocol):
    async def eval(self, script: str, numkeys: int, *keys_and_args: object) -> object: ...

    async def aclose(self) -> None: ...


class RedisRateLimiter:
    '''Coordena limites entre processos sem persistir identidade em texto.'''

    def __init__(
        self, client: AsyncRedisClient, *, key_prefix: str = 'serdial21:rate-limit',
    ) -> None:
        self._client = client
        self._key_prefix = key_prefix.rstrip(':')

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        ca_cert_path: Path | None = None,
        connect_timeout_seconds: int = 3,
        operation_timeout_seconds: int = 3,
    ) -> RedisRateLimiter:
        options: dict[str, object] = {
            'decode_responses': False,
            'socket_connect_timeout': connect_timeout_seconds,
            'socket_timeout': operation_timeout_seconds,
            'health_check_interval': 30,
        }
        if ca_cert_path is not None:
            options['ssl_ca_certs'] = str(ca_cert_path)
            options['ssl_cert_reqs'] = 'required'
        return cls(Redis.from_url(url, **options))

    async def allow(
        self, identity: str, bucket: str, limit: int, window_seconds: int,
    ) -> bool:
        digest = sha256(identity.encode('utf-8')).hexdigest()
        key = f'{self._key_prefix}:{bucket}:{digest}'
        try:
            count = await self._client.eval(
                _ALLOW_SCRIPT, 1, key, window_seconds,
            )
        except RedisError:
            raise RateLimiterUnavailable from None
        return int(count) <= limit

    async def aclose(self) -> None:
        await self._client.aclose()
