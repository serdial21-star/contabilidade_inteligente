'''Contrato HTTP de vivacidade do processo.'''

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

from serdial21.bootstrap.database import DatabaseRuntime
from serdial21.shared_kernel.alerting import (
    AlertDispatcher,
    AlertSeverity,
    OperationalAlert,
)


router = APIRouter(prefix='/health', tags=['health'])


class HealthResponse(BaseModel):
    status: Literal['ok']


class DatabaseHealthResponse(BaseModel):
    status: Literal['ready', 'not_ready']


@router.get('/live', response_model=HealthResponse)
def live(request: Request) -> HealthResponse:
    del request
    return HealthResponse(status='ok')


@router.get(
    '/ready',
    response_model=DatabaseHealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {'model': DatabaseHealthResponse}},
)
def ready(request: Request, response: Response) -> DatabaseHealthResponse:
    database: DatabaseRuntime = request.app.state.database
    if not database.check():
        alerts: AlertDispatcher = request.app.state.alerts
        alerts.emit(OperationalAlert(
            key='database.readiness.unavailable',
            category='DATABASE',
            severity=AlertSeverity.CRITICAL,
            event_name='database.readiness.failed',
            runbook='RECOVERY_RUNBOOK.md#database-unavailable',
        ))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DatabaseHealthResponse(status='not_ready')
    return DatabaseHealthResponse(status='ready')
