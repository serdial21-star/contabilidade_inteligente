'''Endpoint de métricas opt-in, protegido e destinado somente à rede interna.'''

from hmac import compare_digest

from fastapi import APIRouter, Request, status
from fastapi.responses import PlainTextResponse, Response

from serdial21.bootstrap.settings import AppSettings
from serdial21.shared_kernel.observability import MetricsRegistry, security_event


router = APIRouter(prefix='/internal', tags=['operations'])


@router.get('/metrics', include_in_schema=False)
def metrics(request: Request) -> Response:
    settings: AppSettings = request.app.state.settings
    if not settings.metrics_endpoint_enabled or settings.metrics_access_token is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    supplied = request.headers.get('authorization', '')
    expected = f'Bearer {settings.metrics_access_token.get_secret_value()}'
    if not compare_digest(supplied, expected):
        request.app.state.metrics.increment(
            'authorization_denials_total', {'reason': 'metrics_access'}
        )
        security_event('authorization.denied', fields={'reason': 'metrics_access'})
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    registry: MetricsRegistry = request.app.state.metrics
    return PlainTextResponse(
        registry.render_prometheus(),
        media_type='text/plain; version=0.0.4; charset=utf-8',
    )
