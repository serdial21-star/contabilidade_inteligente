'''Entidades puras para a importação determinística de extratos OFX.'''

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BankAccount:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    bank_id: str | None
    branch_id: str | None
    account_number: str
    account_type: str | None
    currency_code: str | None
    external_identity: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class BankStatement:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    bank_account_id: UUID
    artifact_id: UUID
    transformation_run_id: UUID
    schema_version: str
    start_date: date | None
    end_date: date | None
    opening_balance: Decimal | None
    closing_balance: Decimal | None
    currency_code: str | None
    sign_policy: str
    source_hash: str
    fingerprint: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class BankTransaction:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    bank_statement_id: UUID
    bank_account_id: UUID
    fitid: str | None
    external_reference: str | None
    transaction_date: date | None
    posted_date: date | None
    amount: Decimal
    direction: str
    description: str | None
    document_number: str | None
    fingerprint: str
    identity_kind: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ParsedOfxTransaction:
    fitid: str | None
    external_reference: str | None
    transaction_date: date | None
    posted_date: date | None
    amount: Decimal
    direction: str
    description: str | None
    document_number: str | None


@dataclass(frozen=True, slots=True)
class ParsedOfxStatement:
    bank_id: str | None
    branch_id: str | None
    account_number: str
    account_type: str | None
    currency_code: str | None
    start_date: date | None
    end_date: date | None
    opening_balance: Decimal | None
    closing_balance: Decimal | None
    transactions: tuple[ParsedOfxTransaction, ...]


@dataclass(frozen=True, slots=True)
class ParsedOfx:
    schema_version: str
    statements: tuple[ParsedOfxStatement, ...]
