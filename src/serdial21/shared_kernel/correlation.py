'''Contexto técnico isolado por requisição para logs e diagnóstico.'''

from contextvars import ContextVar


correlation_id_context: ContextVar[str | None] = ContextVar(
    'correlation_id',
    default=None,
)
request_id_context: ContextVar[str | None] = ContextVar('request_id', default=None)


def get_correlation_id() -> str | None:
    '''Obtém o identificador da requisição no contexto atual.'''

    return correlation_id_context.get()


def get_request_id() -> str | None:
    '''Obtém o identificador da requisição no contexto atual.'''

    return request_id_context.get()

