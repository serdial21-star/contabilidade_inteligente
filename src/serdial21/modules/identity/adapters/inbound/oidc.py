'''Validação local de access tokens OIDC assinados com RS256.'''

from collections.abc import Callable
from datetime import UTC, datetime
from threading import Lock
from time import monotonic
from typing import Any
from uuid import UUID

import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError, PyJWKError

from serdial21.modules.identity.domain.entities import VerifiedIdentity
from serdial21.shared_kernel.observability import security_event


class AuthenticationError(PermissionError):
    code = 'authentication_failed'

    def __init__(self) -> None:
        super().__init__('authentication failed')


class OidcJwtVerifier:
    '''Fixa algoritmo/issuer/audience e nunca registra token ou claims.'''

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str,
        leeway_seconds: int = 30,
        timeout_seconds: int = 5,
        jwks_lifespan_seconds: int = 300,
        unknown_kid_refresh_cooldown_seconds: int = 60,
        signing_key_resolver: Callable[[str], Any] | None = None,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._issuer = issuer.rstrip('/')
        self._audience = audience
        self._leeway_seconds = leeway_seconds
        self._client = PyJWKClient(
            jwks_url,
            cache_keys=False,
            lifespan=jwks_lifespan_seconds,
            timeout=timeout_seconds,
        )
        self._jwks_refresh_cooldown_seconds = (
            unknown_kid_refresh_cooldown_seconds
        )
        self._clock = clock
        self._last_jwks_refresh_attempt_at: float | None = None
        self._jwks_refresh_lock = Lock()
        self._signing_key_resolver = signing_key_resolver

    def verify(self, token: str) -> VerifiedIdentity:
        if not token or len(token) > 16_384:
            self._deny('malformed_bearer')
        try:
            key = (
                self._signing_key_resolver(token)
                if self._signing_key_resolver is not None
                else self._resolve_signing_key(token)
            )
            claims = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._leeway_seconds,
                options={
                    'require': ['aud', 'exp', 'iat', 'iss', 'sub', 'tenant_id'],
                },
            )
            subject = claims['sub']
            if not isinstance(subject, str) or not subject.strip() or len(subject) > 255:
                self._deny('invalid_subject')
            issued_at = datetime.fromtimestamp(int(claims['iat']), tz=UTC)
            expires_at = datetime.fromtimestamp(int(claims['exp']), tz=UTC)
            return VerifiedIdentity(
                issuer=self._issuer,
                subject=subject,
                tenant_id=UUID(str(claims['tenant_id'])),
                issued_at=issued_at,
                expires_at=expires_at,
            )
        except AuthenticationError:
            raise
        except (InvalidTokenError, PyJWKClientError, PyJWKError, KeyError, TypeError, ValueError):
            self._deny('invalid_token')

    def _resolve_signing_key(self, token: str) -> Any:
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        if not isinstance(kid, str) or not kid or len(kid) > 255:
            raise PyJWKClientError('invalid signing key identifier')

        signing_keys = self._cached_signing_keys()
        if signing_keys is None:
            signing_keys = self._load_jwks_after_expiry()
        signing_key = self._client.match_kid(signing_keys, kid)
        if signing_key is not None:
            return signing_key.key

        # Um kid desconhecido pode forcar refresh remoto. O mesmo lock e
        # cooldown tambem protegem a renovacao de um conjunto expirado quando
        # o endpoint esta indisponivel.
        with self._jwks_refresh_lock:
            signing_keys = self._cached_signing_keys()
            if signing_keys is not None:
                signing_key = self._client.match_kid(signing_keys, kid)
                if signing_key is not None:
                    return signing_key.key

            signing_keys = self._refresh_signing_keys_locked()
            signing_key = self._client.match_kid(signing_keys, kid)
            if signing_key is None:
                raise PyJWKClientError('unknown signing key identifier')
            return signing_key.key

    def _cached_signing_keys(self) -> list[Any] | None:
        cache = getattr(self._client, 'jwk_set_cache', ...)
        if cache is ...:
            # Clientes falsos de teste representam diretamente o cache atual.
            return self._client.get_signing_keys()
        if cache is None or cache.get() is None:
            return None
        return self._client.get_signing_keys()

    def _load_jwks_after_expiry(self) -> list[Any]:
        with self._jwks_refresh_lock:
            signing_keys = self._cached_signing_keys()
            if signing_keys is not None:
                return signing_keys
            return self._refresh_signing_keys_locked()

    def _refresh_signing_keys_locked(self) -> list[Any]:
        now = self._clock()
        last_attempt = self._last_jwks_refresh_attempt_at
        if (
            last_attempt is not None
            and now - last_attempt < self._jwks_refresh_cooldown_seconds
        ):
            raise PyJWKClientError('JWKS refresh cooldown active')
        # Registrar antes do I/O tambem contem falhas e timeouts do endpoint.
        self._last_jwks_refresh_attempt_at = now
        return self._client.get_signing_keys(refresh=True)

    @staticmethod
    def _deny(reason: str) -> None:
        security_event('authentication.denied', fields={'reason': reason})
        raise AuthenticationError()
