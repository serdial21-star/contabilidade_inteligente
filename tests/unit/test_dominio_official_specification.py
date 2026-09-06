from decimal import Decimal
from uuid import uuid4

import pytest

from serdial21.modules.integrations.adapters.outbound.dominio import DominioConnector
from serdial21.modules.integrations.adapters.outbound.dominio_records import (
    DominioRecord6000,
    DominioRecord6100,
    DominioRecord6110,
    DominioRecord6130,
)
from serdial21.modules.integrations.adapters.outbound.dominio_settings import DominioExportSettings
from serdial21.modules.integrations.adapters.outbound.dominio_validation import validate_dominio_structure
from serdial21.modules.integrations.application.ports.connector import (
    ConnectorConfiguration,
    LayoutSpecificationRequiredError,
)


def batch(entry_type: str = 'X') -> DominioRecord6000:
    return DominioRecord6000(entry_type, None, None, None)


def entry() -> DominioRecord6100:
    return DominioRecord6100('unconfirmed', 'debit', 'credit', 'unconfirmed', None, None, None, None, None)


def test_invalid_6000_type_and_orphan_children_are_rejected() -> None:
    with pytest.raises(ValueError, match='tipo'):
        validate_dominio_structure((batch('Z'),))
    with pytest.raises(ValueError, match='6110 exige pai 6100'):
        validate_dominio_structure((batch(), DominioRecord6110(None, None, Decimal('1.00'))))
    with pytest.raises(ValueError, match='6130 exige pai 6100'):
        validate_dominio_structure((batch(), DominioRecord6130(None, Decimal('1.00'))))


def test_confirmed_parent_structure_and_decimal_scale_are_validated() -> None:
    validate_dominio_structure((
        batch(), entry(), DominioRecord6110(None, None, Decimal('1.00')),
        DominioRecord6130(None, Decimal('2.00')),
    ))
    with pytest.raises(ValueError, match='2 casas'):
        validate_dominio_structure((batch(), entry(), DominioRecord6110(None, None, Decimal('1.0'))))


def test_homologation_flag_defaults_false_and_real_connector_export_is_still_blocked() -> None:
    assert DominioExportSettings(_env_file=None).dominio_export_homologated is False
    with pytest.raises(LayoutSpecificationRequiredError):
        DominioConnector().prepare_export(
            {}, ConnectorConfiguration('672', None, None), tenant_id=uuid4(), company_id=uuid4(),
            revision_id=uuid4(), actor_id=uuid4(), correlation_id=uuid4(),
        )
