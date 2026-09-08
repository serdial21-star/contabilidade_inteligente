'''Validação local de access tokens OIDC assinados com RS256.'''

from collections.abc import Callable
from datetime import UTC, datetime
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
        signing_key_resolver: Callable[[str], Any] | None = None,
    ) -> None:
        self._issuer = issuer.rstrip('/')
        self._audience = audience
        self._leeway_seconds = leeway_seconds
        self._client = PyJWKClient(
            jwks_url,
            cache_keys=True,
            max_cached_keys=16,
            lifespan=300,
            timeout=timeout_seconds,
        )
        self._signing_key_resolver = signing_key_resolver

    def verify(self, token: str) -> VerifiedIdentity:
        if not token or len(token) > 16_384:
            self._deny('malformed_bearer')
        try:
            key = (
                self._signing_key_resolver(token)
                if self._signing_key_resolver is not None
                else self._client.get_signing_key_from_jwt(token).key
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

    @staticmethod
    def _deny(reason: str) -> None:
        security_event('authentication.denied', fields={'reason': reason})
        raise AuthenticationError()
