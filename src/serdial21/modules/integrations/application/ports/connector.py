'''Contrato de saída para conectores de sistemas contábeis.

O contrato não presume campos, posições ou codificações de fornecedor. Essas
decisões pertencem a uma LayoutVersion oficial e publicada.
'''

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


class LayoutSpecificationRequiredError(RuntimeError):
    '''Impede exportação enquanto o contrato oficial do destino estiver ausente.'''


@dataclass(frozen=True, slots=True)
class ConnectorConfiguration:
    '''Referências imutáveis para o contrato homologado de um destino.'''

    layout_reference: str | None
    layout_version: str | None
    golden_file_reference: str | None


@dataclass(frozen=True, slots=True)
class ExportPreparation:
    '''Resultado ainda não entregue: lote, bytes validados e hash verificável.'''

    batch_id: UUID
    payload: bytes
    payload_hash: str


class ConnectorPort(Protocol):
    '''Sequência obrigatória para uma exportação externa segura.'''

    def validate_configuration(self, configuration: ConnectorConfiguration) -> None:
        '''Valida configuração e referências do layout antes da transformação.'''

    def convert_to_layout(
        self,
        canonical: Mapping[str, object],
        configuration: ConnectorConfiguration,
    ) -> bytes:
        '''Transforma o canônico segundo uma LayoutVersion publicada.'''

    def validate_output(
        self,
        payload: bytes,
        configuration: ConnectorConfiguration,
    ) -> None:
        '''Valida o arquivo antes de ele poder ser disponibilizado.'''

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
        '''Registra lote, hash e auditoria em transação coordenada pela aplicação.'''
