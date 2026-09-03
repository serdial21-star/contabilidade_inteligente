'''Registro explícito dos models ORM conhecidos pelo Alembic.'''


def load_models() -> None:
    from serdial21.modules.access_control.adapters.outbound.persistence import models

    _ = models

