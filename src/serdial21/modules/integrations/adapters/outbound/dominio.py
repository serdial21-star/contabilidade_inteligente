'''Estrutura fail-closed do conector Domínio Sistemas.

Nenhum layout oficial, versão identificada ou golden file foi fornecido ao
projeto. Portanto, este adaptador não codifica campos, delimitadores, posições,
tamanhos, códigos, encoding ou extensão de arquivo.
'''

from collections.abc import Mapping
from uuid import UUID

from serdial21.modules.integrations.application.ports.connector import (
    ConnectorConfiguration,
    ExportPreparation,
    LayoutSpecificationRequiredError,
)


PENDING_LAYOUT_REQUIREMENTS = (
    'identificação da versão do Domínio Sistemas',
    'especificação oficial do fluxo TXT selecionado',
    'mapeamento do modelo canônico para os campos do layout',
    'regras oficiais de validação e de codificação',
    'golden files homologados e respectivos resultados esperados',
)


class DominioConnector:
    '''Adapter reservado ao contrato oficial do Domínio Sistemas.

    A futura implementação usará as portas de layout, persistência de
    ExportBatch e auditoria da aplicação. Enquanto os insumos oficiais não
    existirem, cada etapa que poderia produzir ou disponibilizar um arquivo
    falha antes de qualquer transformação.
    '''

    name = 'dominio-sistemas'

    def validate_configuration(self, configuration: ConnectorConfiguration) -> None:
        del configuration
        raise LayoutSpecificationRequiredError(_pending_message())

    def convert_to_layout(
        self,
        canonical: Mapping[str, object],
        configuration: ConnectorConfiguration,
    ) -> bytes:
        del canonical, configuration
        raise LayoutSpecificationRequiredError(_pending_message())

    def validate_output(
        self,
        payload: bytes,
        configuration: ConnectorConfiguration,
    ) -> None:
        del payload, configuration
        raise LayoutSpecificationRequiredError(_pending_message())

    def prepare_export(
        self,
        canonical: Mapping[str, object],
        configuration: ConnectorConfiguration,
        *,
        tenant_id: UUID,
        company_id: UUID,
        revision_id: UUID,
        actor_id: UUID,
        correlation_id: UUID,
    ) -> ExportPreparation:
        del canonical, configuration, tenant_id, company_id
        del revision_id, actor_id, correlation_id
        raise LayoutSpecificationRequiredError(_pending_message())


def _pending_message() -> str:
    requirements = '; '.join(PENDING_LAYOUT_REQUIREMENTS)
    return f'PENDÊNCIA: DOCUMENTAÇÃO DE LAYOUT DOMÍNIO NECESSÁRIA. Faltam: {requirements}.'
