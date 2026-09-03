'''Contexto técnico de correlação de requisições.'''

from contextvars import ContextVar


correlation_id_context: ContextVar[str | None] = ContextVar(
    'correlation_id',
    default=None,
)


def get_correlation_id() -> str | None:
    '''Obtém o identificador da requisição no contexto atual.'''

    return correlation_id_context.get()

