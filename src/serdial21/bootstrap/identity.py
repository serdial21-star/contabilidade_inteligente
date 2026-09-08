'''Composição do verificador OIDC externo.'''

from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.identity.adapters.inbound.oidc import OidcJwtVerifier


def build_oidc_verifier(settings: AppSettings) -> OidcJwtVerifier | None:
    if not settings.oidc_configured:
        return None
    assert settings.oidc_issuer is not None
    assert settings.oidc_audience is not None
    assert settings.oidc_jwks_url is not None
    return OidcJwtVerifier(
        issuer=settings.oidc_issuer,
        audience=settings.oidc_audience,
        jwks_url=str(settings.oidc_jwks_url),
        leeway_seconds=settings.oidc_clock_skew_seconds,
        timeout_seconds=settings.oidc_jwks_timeout_seconds,
    )
