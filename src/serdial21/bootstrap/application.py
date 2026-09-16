'''Fábrica da aplicação HTTP.'''

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from serdial21 import __version__
from serdial21.bootstrap.database import DatabaseRuntime
from serdial21.bootstrap.settings import AppSettings, get_settings
from serdial21.bootstrap.identity import build_oidc_verifier
from serdial21.entrypoints.http.middleware.correlation_id import (
    CorrelationIdMiddleware,
)
from serdial21.entrypoints.http.middleware.security_headers import (
    SecurityHeadersMiddleware,
)
from serdial21.entrypoints.http.middleware.request_observability import (
    RequestObservabilityMiddleware,
)
from serdial21.entrypoints.http.middleware.rate_limit import (
    InMemoryRateLimiter, RateLimiter, RateLimitMiddleware,
)
from serdial21.entrypoints.http.middleware.request_limits import (
    RequestBodyLimitMiddleware,
)
from serdial21.entrypoints.http.routes.health import router as health_router
from serdial21.entrypoints.http.routes.identity import router as identity_router
from serdial21.entrypoints.http.routes.catalog import router as catalog_router
from serdial21.entrypoints.http.routes.operations import router as operations_router
from serdial21.entrypoints.http.routes.observability import router as observability_router
from serdial21.shared_kernel.alerting import AlertDispatcher, AlertSink, NullAlertSink
from serdial21.shared_kernel.observability import (
    MetricsRegistry,
    configure_technical_logging,
    technical_event,
)


def create_app(
    settings: AppSettings | None = None, *, rate_limiter: RateLimiter | None = None,
    alert_sink: AlertSink | None = None,
) -> FastAPI:
    '''Compõe adaptadores e configurações sem incluir regra de negócio.'''

    resolved_settings = settings or get_settings()
    database = DatabaseRuntime.from_settings(resolved_settings)
    metrics = MetricsRegistry()
    configure_technical_logging(
        resolved_settings.log_level,
        service='serdial21-api',
        environment=resolved_settings.environment,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        technical_event('service.started', fields={
            'environment': resolved_settings.environment,
            'security_mode': 'fail_closed' if resolved_settings.environment in {'homologation', 'production'} else 'local',
            'metrics_enabled': resolved_settings.metrics_endpoint_enabled,
            'rate_limit_backend': resolved_settings.rate_limit_backend,
        })
        try:
            yield
        finally:
            database.dispose()
            technical_event('service.stopped')

    docs_enabled = resolved_settings.resolved_api_docs_enabled
    app = FastAPI(
        title=resolved_settings.app_name,
        version=__version__,
        debug=resolved_settings.debug,
        lifespan=lifespan,
        docs_url='/docs' if docs_enabled else None,
        redoc_url='/redoc' if docs_enabled else None,
        openapi_url='/openapi.json' if docs_enabled else None,
    )
    app.state.settings = resolved_settings
    app.state.database = database
    app.state.metrics = metrics
    app.state.alerts = AlertDispatcher(alert_sink or NullAlertSink())
    app.state.oidc_verifier = build_oidc_verifier(resolved_settings)
    if rate_limiter is None:
        if resolved_settings.rate_limit_backend == 'distributed':
            raise ValueError('distributed rate limiter adapter is required')
        rate_limiter = InMemoryRateLimiter()
    app.add_middleware(
        RequestBodyLimitMiddleware,
        api_prefix=resolved_settings.api_prefix,
        general_limit=resolved_settings.general_request_max_bytes,
        nfe_limit=resolved_settings.nfe_max_xml_bytes,
        ofx_limit=resolved_settings.ofx_max_upload_bytes,
        metrics=metrics,
    )
    app.add_middleware(
        RateLimitMiddleware, limiter=rate_limiter,
        general_limit=resolved_settings.rate_limit_general_per_minute,
        sensitive_limit=resolved_settings.rate_limit_sensitive_per_minute,
        upload_limit=resolved_settings.rate_limit_upload_per_minute,
        metrics=metrics,
    )
    if resolved_settings.resolved_trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=list(resolved_settings.resolved_trusted_hosts),
        )
    if resolved_settings.resolved_cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.resolved_cors_allowed_origins),
            allow_credentials=False,
            allow_methods=['GET', 'POST', 'OPTIONS'],
            allow_headers=[
                'Authorization', 'Content-Type', 'Idempotency-Key',
                'X-Filename', 'X-Correlation-ID',
            ],
            expose_headers=['X-Correlation-ID', 'X-Request-ID'],
            max_age=600,
        )
    app.add_middleware(
        SecurityHeadersMiddleware,
        hsts_enabled=resolved_settings.environment == 'production',
        hsts_max_age_seconds=resolved_settings.hsts_max_age_seconds,
    )
    app.add_middleware(RequestObservabilityMiddleware, metrics=metrics)
    app.add_middleware(CorrelationIdMiddleware)

    if resolved_settings.environment in {'homologation', 'production'}:
        @app.exception_handler(Exception)
        async def safe_unhandled_error(_: Request, __: Exception) -> JSONResponse:
            return JSONResponse(status_code=500, content={'detail': 'internal server error'})
    app.include_router(health_router, prefix=resolved_settings.api_prefix)
    app.include_router(identity_router, prefix=resolved_settings.api_prefix)
    app.include_router(catalog_router, prefix=resolved_settings.api_prefix)
    app.include_router(operations_router, prefix=resolved_settings.api_prefix)
    app.include_router(observability_router)
    return app
