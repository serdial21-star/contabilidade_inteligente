'''Registro explícito dos models ORM conhecidos pelo Alembic.'''


def load_models() -> None:
    from serdial21.modules.access_control.adapters.outbound.persistence import models
    from serdial21.modules.audit.adapters.outbound.persistence import models as audit_models
    from serdial21.modules.intake_documents.adapters.outbound.persistence import (
        models as intake_models,
    )
    from serdial21.bootstrap.audit import install_audit_hooks

    _ = (models, audit_models, intake_models)
    install_audit_hooks()
