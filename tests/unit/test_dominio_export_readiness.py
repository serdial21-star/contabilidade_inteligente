from dataclasses import asdict
from uuid import uuid4

import pytest

from serdial21.modules.integrations.adapters.outbound.dominio import DominioConnector
from serdial21.modules.integrations.adapters.outbound.dominio_layout_models import (
    DominioBatch6000,
    DominioCostCenter6110,
    DominioDfc6130,
    DominioEntry6100,
)
from serdial21.modules.integrations.adapters.outbound.dominio_readiness import (
    DominioExportNotReadyError,
    DominioExportReadiness,
    assert_dominio_export_ready,
)
from serdial21.modules.integrations.application.ports.connector import (
    ConnectorConfiguration,
    LayoutSpecificationRequiredError,
)


@pytest.mark.parametrize('change,code', (
    ({'layout_version_approved': False}, 'LAYOUT_VERSION_NOT_APPROVED'),
    ({'golden_file_registered': False}, 'GOLDEN_FILE_NOT_REGISTERED'),
    ({'mandatory_mapping_complete': False}, 'MANDATORY_MAPPING_INCOMPLETE'),
    ({'proposal_approved': False}, 'PROPOSAL_NOT_APPROVED'),
    ({'accounting_lock_active': True}, 'ACCOUNTING_LOCK_ACTIVE'),
))
def test_export_gate_rejects_each_mandatory_control(change: dict[str, bool], code: str) -> None:
    values = {
        'layout_version_approved': True,
        'golden_file_registered': True,
        'mandatory_mapping_complete': True,
        'proposal_approved': True,
        'accounting_lock_active': False,
    }
    values.update(change)
    with pytest.raises(DominioExportNotReadyError, match=code):
        assert_dominio_export_ready(DominioExportReadiness(**values))


def test_connector_still_refuses_to_generate_txt_without_complete_official_specification() -> None:
    connector = DominioConnector()
    configuration = ConnectorConfiguration('official-source', 'unreviewed-version', None)
    with pytest.raises(LayoutSpecificationRequiredError, match='DOCUMENTAÇÃO DE LAYOUT DOMÍNIO NECESSÁRIA'):
        connector.prepare_export({}, configuration, tenant_id=uuid4(), company_id=uuid4(),
                                 revision_id=uuid4(), actor_id=uuid4(), correlation_id=uuid4())


def test_official_record_models_have_no_unconfirmed_serialized_fields() -> None:
    assert [item.record_code for item in (
        DominioBatch6000(), DominioEntry6100(), DominioCostCenter6110(), DominioDfc6130(),
    )] == ['6000', '6100', '6110', '6130']
    assert asdict(DominioBatch6000()) == {}
