'''Contrato do conector Domínio enquanto o layout oficial não foi fornecido.'''

from uuid import uuid4

import pytest

from serdial21.modules.integrations.adapters.outbound.dominio import (
    DominioConnector,
    PENDING_LAYOUT_REQUIREMENTS,
)
from serdial21.modules.integrations.application.ports.connector import (
    ConnectorConfiguration,
    LayoutSpecificationRequiredError,
)


def _configuration() -> ConnectorConfiguration:
    return ConnectorConfiguration(
        layout_reference=None,
        layout_version=None,
        golden_file_reference=None,
    )


def test_dominio_connector_exposes_the_generic_connector_contract() -> None:
    connector = DominioConnector()

    for method in (
        'validate_configuration',
        'convert_to_layout',
        'validate_output',
        'prepare_export',
    ):
        assert callable(getattr(connector, method))


def test_dominio_connector_fails_closed_before_mapping_or_file_generation() -> None:
    connector = DominioConnector()

    with pytest.raises(
        LayoutSpecificationRequiredError,
        match='PENDÊNCIA: DOCUMENTAÇÃO DE LAYOUT DOMÍNIO NECESSÁRIA',
    ):
        connector.convert_to_layout({'unverified_field': 'value'}, _configuration())


def test_dominio_connector_cannot_register_or_audit_a_fictitious_export() -> None:
    connector = DominioConnector()

    with pytest.raises(LayoutSpecificationRequiredError):
        connector.prepare_export(
            {},
            _configuration(),
            tenant_id=uuid4(),
            company_id=uuid4(),
            revision_id=uuid4(),
            actor_id=uuid4(),
            correlation_id=uuid4(),
        )


def test_documentation_dependencies_are_explicit() -> None:
    assert PENDING_LAYOUT_REQUIREMENTS == (
        'identificação da versão do Domínio Sistemas',
        'especificação oficial do fluxo TXT selecionado',
        'mapeamento do modelo canônico para os campos do layout',
        'regras oficiais de validação e de codificação',
        'golden files homologados e respectivos resultados esperados',
    )
