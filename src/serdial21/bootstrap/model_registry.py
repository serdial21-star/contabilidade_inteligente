'''Registro explícito dos models ORM conhecidos pelo Alembic.'''


def load_models() -> None:
    from serdial21.modules.access_control.adapters.outbound.persistence import models
    from serdial21.modules.audit.adapters.outbound.persistence import models as audit_models
    from serdial21.modules.intake_documents.adapters.outbound.persistence import (
        models as intake_models,
    )
    from serdial21.modules.fiscal_documents.adapters.outbound.persistence import (
        models as fiscal_models,
    )
    from serdial21.modules.banking.adapters.outbound.persistence import models as banking_models
    from serdial21.modules.workflow.adapters.outbound.persistence import models as workflow_models
    from serdial21.modules.workflow.adapters.outbound.persistence import journeys as journey_models
    from serdial21.modules.locks.adapters.outbound.persistence import models as lock_models
    from serdial21.modules.catalog.adapters.outbound.persistence import models as catalog_models
    from serdial21.modules.privacy.adapters.outbound.persistence import models as privacy_models
    from serdial21.bootstrap.audit import install_audit_hooks

    _ = (
        models, audit_models, intake_models, fiscal_models, banking_models,
        workflow_models, journey_models, lock_models, catalog_models, privacy_models,
    )
    install_audit_hooks()
