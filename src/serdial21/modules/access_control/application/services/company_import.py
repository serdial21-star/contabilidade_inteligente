'''Import manual e idempotente de empresas externas (ADR 0013).

Regras puras de mapeamento ficam isoladas de I/O para permitir teste sem
banco. A execução (busca/gravação) usa uma porta estreita, específica deste
caso de uso, e nunca lê ou grava o campo de senha do sistema de origem.
'''

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


EXTERNAL_SYSTEM_SISTEMA_A = 'sistema_a'
CLIENT_EXTERNAL_TYPE = 'cliente'
IMPORT_DEFAULT_TIMEZONE = 'America/Sao_Paulo'
IMPORT_DEFAULT_CURRENCY_CODE = 'BRL'

_STATUS_MAP = {
    'Ativo': 'active',
    'Inativo': 'inactive',
}


def clean_external_cell(value: str | None) -> str | None:
    '''Exportações do phpMyAdmin gravam NULL como o texto literal `NULL`.'''

    stripped = (value or '').strip()
    return None if not stripped or stripped.upper() == 'NULL' else stripped


@dataclass(frozen=True, slots=True)
class ExternalClientRecord:
    '''Linha crua da tabela `clientes` do Sistema A (somente campos usados).'''

    external_id: str
    nome_cliente: str
    nome_fantasia: str | None
    cnpj: str | None
    cnpj_cpf: str | None
    status: str


@dataclass(frozen=True, slots=True)
class MappedCompany:
    external_type: str
    external_id: str
    legal_name: str
    trade_name: str | None
    tax_identifier: str
    status: str


@dataclass(frozen=True, slots=True)
class SkippedRecord:
    external_id: str
    reason: str


def map_external_client(record: ExternalClientRecord) -> MappedCompany | SkippedRecord:
    '''Decisão pura de mapeamento; não faz I/O e não inventa dado ausente.'''

    mapped_status = _STATUS_MAP.get(record.status)
    if mapped_status is None:
        return SkippedRecord(record.external_id, reason=f'status_nao_mapeado:{record.status}')

    raw_tax_identifier = (record.cnpj or '').strip() or (record.cnpj_cpf or '').strip()
    tax_identifier = ''.join(char for char in raw_tax_identifier if char.isdigit())
    if not tax_identifier:
        return SkippedRecord(record.external_id, reason='sem_identificador_fiscal')
    if len(tax_identifier) not in (11, 14):
        return SkippedRecord(record.external_id, reason='identificador_fiscal_invalido')

    return MappedCompany(
        external_type=CLIENT_EXTERNAL_TYPE,
        external_id=record.external_id,
        legal_name=record.nome_cliente.strip(),
        trade_name=(record.nome_fantasia or '').strip() or None,
        tax_identifier=tax_identifier,
        status=mapped_status,
    )


@dataclass(frozen=True, slots=True)
class CompanySnapshot:
    id: UUID
    legal_name: str
    trade_name: str | None
    tax_identifier: str
    status: str
    external_id: str | None


@dataclass(frozen=True, slots=True)
class ConflictDetail:
    external_id: str
    reason: str


class CompanyImportRepository(Protocol):
    def find_by_external_reference(
        self, tenant_id: UUID, external_system: str, external_type: str, external_id: str,
    ) -> CompanySnapshot | None: ...

    def find_by_tax_identifier(
        self, tenant_id: UUID, tax_identifier: str,
    ) -> CompanySnapshot | None: ...

    def create(
        self, tenant_id: UUID, mapped: MappedCompany, *, external_system: str, now: datetime,
    ) -> UUID: ...


@dataclass(frozen=True, slots=True)
class ImportReport:
    created: tuple[UUID, ...]
    unchanged: tuple[str, ...]
    conflicts: tuple[ConflictDetail, ...]
    skipped: tuple[SkippedRecord, ...]


class ImportExternalCompanies:
    '''Executa o import descrito no ADR 0013: aditivo, sem sobrescrita silenciosa.'''

    def __init__(self, repository: CompanyImportRepository) -> None:
        self._repository = repository

    def execute(
        self, tenant_id: UUID, records: list[ExternalClientRecord], *, now: datetime,
    ) -> ImportReport:
        created: list[UUID] = []
        unchanged: list[str] = []
        conflicts: list[ConflictDetail] = []
        skipped: list[SkippedRecord] = []

        for record in records:
            decision = map_external_client(record)
            if isinstance(decision, SkippedRecord):
                skipped.append(decision)
                continue

            existing = self._repository.find_by_external_reference(
                tenant_id, EXTERNAL_SYSTEM_SISTEMA_A, decision.external_type, decision.external_id,
            )
            if existing is not None:
                if (
                    existing.legal_name == decision.legal_name
                    and existing.trade_name == decision.trade_name
                    and existing.tax_identifier == decision.tax_identifier
                    and existing.status == decision.status
                ):
                    unchanged.append(decision.external_id)
                else:
                    conflicts.append(ConflictDetail(decision.external_id, 'conteudo_divergente'))
                continue

            tax_conflict = self._repository.find_by_tax_identifier(
                tenant_id, decision.tax_identifier,
            )
            if tax_conflict is not None and tax_conflict.external_id != decision.external_id:
                conflicts.append(ConflictDetail(decision.external_id, 'identificador_fiscal_em_uso'))
                continue

            created_id = self._repository.create(
                tenant_id, decision, external_system=EXTERNAL_SYSTEM_SISTEMA_A, now=now,
            )
            created.append(created_id)

        return ImportReport(
            created=tuple(created),
            unchanged=tuple(unchanged),
            conflicts=tuple(conflicts),
            skipped=tuple(skipped),
        )
