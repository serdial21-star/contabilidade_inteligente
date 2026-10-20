'''Composição do verificador de login: ponte do Sistema A (OIDC) e login único S21 (T-0012).'''

from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.identity.adapters.inbound.oidc import (
    IssuerRoutingVerifier,
    OidcJwtVerifier,
    s21_login_claims_acceptable,
)


def _common(settings: AppSettings) -> dict[str, int]:
    return {
        'leeway_seconds': settings.oidc_clock_skew_seconds,
        'timeout_seconds': settings.oidc_jwks_timeout_seconds,
        'jwks_lifespan_seconds': settings.oidc_jwks_cache_lifespan_seconds,
        'unknown_kid_refresh_cooldown_seconds': settings.oidc_unknown_kid_refresh_cooldown_seconds,
    }


def build_oidc_verifier(settings: AppSettings) -> OidcJwtVerifier | IssuerRoutingVerifier | None:
    verifiers: dict[str, OidcJwtVerifier] = {}
    if settings.oidc_configured:
        assert settings.oidc_issuer is not None
        assert settings.oidc_audience is not None
        assert settings.oidc_jwks_url is not None
        verifiers[settings.oidc_issuer] = OidcJwtVerifier(
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            jwks_url=str(settings.oidc_jwks_url),
            **_common(settings),
        )
    if settings.s21_login_configured:
        issuer = settings.s21_login_issuer
        assert issuer is not None
        verifiers[issuer] = OidcJwtVerifier(
            issuer=issuer,
            audience='authenticated',
            jwks_url=issuer + '/.well-known/jwks.json',
            fixed_tenant_id=settings.s21_login_tenant_id,
            claims_check=s21_login_claims_acceptable,
            **_common(settings),
        )
    if not verifiers:
        return None
    if len(verifiers) == 1 and settings.oidc_configured:
        return next(iter(verifiers.values()))
    return IssuerRoutingVerifier(verifiers)
