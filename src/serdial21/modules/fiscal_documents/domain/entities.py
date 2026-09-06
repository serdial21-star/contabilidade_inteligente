'''Entidades imutáveis do primeiro canônico de NF-e modelo 55.'''

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CanonicalRecord:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    artifact_id: UUID
    transformation_run_id: UUID
    record_type: str
    schema_version: str
    external_identity: str
    source_hash: str
    fingerprint: str
    fact_at: datetime | None
    status: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class FiscalDocument:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    canonical_record_id: UUID
    artifact_id: UUID
    access_key: str
    model: str
    schema_version: str
    series: str | None
    document_number: str | None
    operation_nature: str | None
    issuer_tax_id: str | None
    issuer_name: str | None
    recipient_tax_id: str | None
    recipient_name: str | None
    issued_at: datetime | None
    movement_at: datetime | None
    products_total: Decimal | None
    freight_total: Decimal | None
    insurance_total: Decimal | None
    discount_total: Decimal | None
    other_total: Decimal | None
    tax_total: Decimal | None
    invoice_total: Decimal | None
    observed_status: str
    protocol_status_code: str | None
    protocol_status_reason: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class FiscalDocumentItem:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    fiscal_document_id: UUID
    sequence: int
    product_code: str | None
    description: str | None
    ncm: str | None
    cfop: str | None
    commercial_unit: str | None
    quantity: Decimal | None
    unit_value: Decimal | None
    gross_total: Decimal | None
    discount_total: Decimal | None
    other_total: Decimal | None
    included_in_total: bool | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TaxDetail:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    fiscal_document_item_id: UUID
    tax_type: str
    tax_status: str | None
    calculation_base: Decimal | None
    rate: Decimal | None
    amount: Decimal | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ParsedTaxDetail:
    tax_type: str
    tax_status: str | None
    calculation_base: Decimal | None
    rate: Decimal | None
    amount: Decimal | None


@dataclass(frozen=True, slots=True)
class ParsedFiscalItem:
    sequence: int
    product_code: str | None
    description: str | None
    ncm: str | None
    cfop: str | None
    commercial_unit: str | None
    quantity: Decimal | None
    unit_value: Decimal | None
    gross_total: Decimal | None
    discount_total: Decimal | None
    other_total: Decimal | None
    included_in_total: bool | None
    taxes: tuple[ParsedTaxDetail, ...]


@dataclass(frozen=True, slots=True)
class ParsedValidationIssue:
    code: str
    severity: str
    field_path: str | None
    message: str


@dataclass(frozen=True, slots=True)
class ParsedNFe55:
    access_key: str
    model: str
    schema_version: str
    series: str | None
    document_number: str | None
    operation_nature: str | None
    issuer_tax_id: str | None
    issuer_name: str | None
    recipient_tax_id: str | None
    recipient_name: str | None
    issued_at: datetime | None
    movement_at: datetime | None
    products_total: Decimal | None
    freight_total: Decimal | None
    insurance_total: Decimal | None
    discount_total: Decimal | None
    other_total: Decimal | None
    tax_total: Decimal | None
    invoice_total: Decimal | None
    observed_status: str
    protocol_status_code: str | None
    protocol_status_reason: str | None
    items: tuple[ParsedFiscalItem, ...]
    issues: tuple[ParsedValidationIssue, ...]
