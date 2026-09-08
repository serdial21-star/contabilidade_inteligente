"""Contratos internos da jornada; snapshots de domínio não são modelos de API."""
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from serdial21.modules.accounting.domain.entities import (
    AccountingProposal, JournalEntryRevision, JournalLine, JournalEntrySourceLink,
)
from serdial21.modules.chart_of_accounts.domain.entities import AccountVersion, Ledger
from serdial21.modules.fiscal_documents.application.services.nfe55_importer import NFe55ImportResult
from serdial21.modules.integrations.application.ports.connector import ConnectorConfiguration
from serdial21.modules.integrations.domain.entities import ExportBatch
from serdial21.modules.locks.domain.entities import AccountLock
from serdial21.modules.rules.domain.entities import AccountingRuleVersion, RuleEvaluation, RuleSetRelease
from serdial21.modules.workflow.domain.entities import (
    ApprovalDecision, ApprovalRequest, ApprovalStep, AuthorizedEffect,
    WorkflowCase, WorkflowVersion, WorkItem, WorkItemSubject,
)


class JourneyConflictError(RuntimeError):
    code = 'journey_conflict'


class JourneyUnavailableError(LookupError):
    code = 'resource_unavailable'

    def __init__(self) -> None:
        super().__init__('resource unavailable')


class JourneyNotReadyError(ValueError):
    code = 'journey_not_ready'


@dataclass(frozen=True, slots=True)
class PostingPolicy:
    """Escolhas explícitas e versionadas do catálogo; nenhuma regra padrão."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    status: str
    amount_field: str
    decimal_places: int


@dataclass(frozen=True, slots=True)
class PreparationPlan:
    release: RuleSetRelease
    rules: tuple[AccountingRuleVersion, ...]
    accounts: tuple[AccountVersion, ...]
    ledger: Ledger
    posting: PostingPolicy
    workflow: WorkflowVersion
    # Hierarquia completa fornecida pelo catálogo de contas para os locks.
    account_groups: tuple[tuple[UUID, tuple[UUID, ...]], ...]
    # Defaults preservam leitura de checkpoints anteriores à migration 0011.
    approval_role: str = 'CONTADOR'
    responsible_role: str = 'CONTADOR'


@dataclass(frozen=True, slots=True)
class JourneyCommand:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID
    idempotency_key: str
    accounting_date: date
    period_start: date
    period_end: date
    approval_expires_at: datetime


@dataclass(frozen=True, slots=True)
class Journey:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    correlation_id: UUID
    idempotency_key: str
    command_hash: str
    version: int
    status: str
    proposer_id: UUID
    imported: NFe55ImportResult
    plan: PreparationPlan | None = None
    evaluation: RuleEvaluation | None = None
    proposal: AccountingProposal | None = None
    revision: JournalEntryRevision | None = None
    lines: tuple[JournalLine, ...] = ()
    sources: tuple[JournalEntrySourceLink, ...] = ()
    revision_hash: str | None = None
    validation_status: str | None = None
    case: WorkflowCase | None = None
    item: WorkItem | None = None
    subject: WorkItemSubject | None = None
    request: ApprovalRequest | None = None
    step: ApprovalStep | None = None
    decision: ApprovalDecision | None = None
    # A chave pertence ao comando humano que produziu a decisão. Ela é
    # persistida no checkpoint imutável para tornar seguro o retry da borda.
    decision_idempotency_key: str | None = None
    decision_payload_hash: str | None = None
    effect: AuthorizedEffect | None = None
    batch: ExportBatch | None = None
    connector_configuration: ConnectorConfiguration | None = None

    def advance(self, **changes: object) -> 'Journey':
        return replace(self, version=self.version + 1, **changes)


class JourneyRepository(Protocol):
    """Checkpoint + auditoria compartilham a transação do chamador.

    append exige versão consecutiva e exclusão mútua por jornada. Histórico é
    imutável; qualquer falha requer rollback da unidade de trabalho.
    """
    def find_by_key(self, tenant_id: UUID, company_id: UUID, key: str) -> Journey | None: ...
    def get(self, tenant_id: UUID, company_id: UUID, journey_id: UUID) -> Journey | None: ...
    def find_by_export(self, tenant_id: UUID, company_id: UUID, batch_id: UUID) -> Journey | None: ...
    def append(self, journey: Journey) -> None: ...


class JourneyCatalog(Protocol):
    """Porta confiável para versões publicadas; nunca recebe configuração HTTP crua.

    A implementação deve ler estado atual sob a mesma unidade de trabalho e
    coordenar locks com seus escritores até o commit. Não há catálogo permissivo
    ou regra contábil de conveniência no bootstrap.
    """
    def preparation(
        self, tenant_id: UUID, company_id: UUID, at: date | None = None,
    ) -> PreparationPlan | None: ...
    def locks(self, tenant_id: UUID, company_id: UUID) -> tuple[AccountLock, ...]: ...

