'''Especificação explícita do catálogo; não contém defaults contábeis.'''

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


CATALOG_STATES = frozenset({'DRAFT', 'REVIEW', 'PUBLISHED'})


@dataclass(frozen=True, slots=True)
class AccountSpec:
    key: str
    code: str
    name: str
    nature: str
    normal_balance: str
    parent_key: str | None
    is_synthetic: bool
    is_postable: bool


@dataclass(frozen=True, slots=True)
class RuleSpec:
    key: str
    name: str
    scope: str
    conditions: tuple[tuple[str, str, str], ...]
    priority: int
    debit_account_key: str
    credit_account_key: str
    automation_level: str
    tests_passed: bool


@dataclass(frozen=True, slots=True)
class MappingEntrySpec:
    key: str
    priority: int
    target_account_key: str
    external_code: str | None = None
    history_contains: str | None = None
    dimension_code: str | None = None
    canonical_entity: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowSpec:
    name: str
    approval_role: str
    responsible_role: str


@dataclass(frozen=True, slots=True)
class CatalogSpec:
    name: str
    ledger_name: str
    currency_code: str
    chart_name: str
    accounts: tuple[AccountSpec, ...]
    rules: tuple[RuleSpec, ...]
    mapping_name: str
    mapping_namespace: str
    mappings: tuple[MappingEntrySpec, ...]
    workflow: WorkflowSpec
    amount_field: str
    decimal_places: int
    valid_from: date
    valid_to: date | None


@dataclass(frozen=True, slots=True)
class CatalogVersion:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    catalog_id: UUID
    supersedes_version_id: UUID | None
    version_no: int
    status: str
    valid_from: date
    valid_to: date | None
    content_hash: str
    created_by: UUID
    reviewed_by: UUID | None
    published_by: UUID | None
    created_at: datetime
    reviewed_at: datetime | None
    published_at: datetime | None


class CatalogConflictError(RuntimeError):
    pass


class CatalogUnavailableError(LookupError):
    def __init__(self) -> None:
        super().__init__('resource unavailable')
