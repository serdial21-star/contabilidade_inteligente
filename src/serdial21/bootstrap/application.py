'''Fábrica da aplicação HTTP.'''

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from serdial21 import __version__
from serdial21.bootstrap.database import DatabaseRuntime
from serdial21.bootstrap.settings import AppSettings, get_settings
from serdial21.entrypoints.http.middleware.correlation_id import (
    CorrelationIdMiddleware,
)
from serdial21.entrypoints.http.routes.health import router as health_router


def create_app(settings: AppSettings | None = None) -> FastAPI:
    '''Compõe adaptadores e configurações sem incluir regra de negócio.'''

    resolved_settings = settings or get_settings()
    database = DatabaseRuntime.from_settings(resolved_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            database.dispose()

    app = FastAPI(
        title=resolved_settings.app_name,
        version=__version__,
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.database = database
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(health_router, prefix=resolved_settings.api_prefix)
    return app
