'''Contrato HTTP de vivacidade do processo.'''

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

from serdial21 import __version__
from serdial21.bootstrap.database import DatabaseRuntime
from serdial21.bootstrap.settings import AppSettings


router = APIRouter(prefix='/health', tags=['health'])


class HealthResponse(BaseModel):
    status: Literal['ok']
    service: str
    environment: str
    version: str


class DatabaseHealthResponse(BaseModel):
    status: Literal['ok', 'unavailable']
    service: Literal['database']


@router.get('/live', response_model=HealthResponse)
def live(request: Request) -> HealthResponse:
    settings: AppSettings = request.app.state.settings
    return HealthResponse(
        status='ok',
        service=settings.app_name,
        environment=settings.environment,
        version=__version__,
    )


@router.get(
    '/ready',
    response_model=DatabaseHealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {'model': DatabaseHealthResponse}},
)
def ready(request: Request, response: Response) -> DatabaseHealthResponse:
    database: DatabaseRuntime = request.app.state.database
    if not database.check():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DatabaseHealthResponse(status='unavailable', service='database')
    return DatabaseHealthResponse(status='ok', service='database')
