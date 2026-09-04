'''Entidades de evidência, recebimento, transformação e linhagem.'''

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EvidenceArtifact:
    id: UUID
    tenant_id: UUID
    content_hash: str
    hash_algorithm: str
    storage_key: str
    media_type: str
    size_bytes: int
    classification: str
    captured_at: datetime
    verified_at: datetime


@dataclass(frozen=True, slots=True)
class ArtifactReceipt:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    batch_id: UUID
    artifact_id: UUID
    original_filename: str
    channel: str
    external_key: str | None
    result: str
    received_at: datetime


@dataclass(frozen=True, slots=True)
class ImportBatch:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    source: str
    idempotency_key: str
    status: str
    total_items: int
    received_items: int
    duplicate_items: int
    failed_items: int
    started_at: datetime
    completed_at: datetime | None
    revision: int


@dataclass(frozen=True, slots=True)
class ImportItem:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    batch_id: UUID
    receipt_id: UUID
    sequence: int
    status: str
    error_code: str | None
    created_subject_type: str | None
    created_subject_id: UUID | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TransformationRun:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    artifact_id: UUID
    previous_run_id: UUID | None
    parser_name: str
    parser_version: str
    schema_version: str | None
    input_hash: str
    output_hash: str | None
    status: str
    started_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    transformation_run_id: UUID
    code: str
    severity: str
    field_path: str | None
    rule_reference: str | None
    message: str
    resolution_status: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class LineageEdge:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    source_type: str
    source_id: UUID
    source_version: int | None
    target_type: str
    target_id: UUID
    target_version: int | None
    transformation_run_id: UUID | None
    relation: str
    created_at: datetime

    def __post_init__(self) -> None:
        if (
            self.source_type == self.target_type
            and self.source_id == self.target_id
            and self.source_version == self.target_version
        ):
            raise ValueError('linhagem não pode apontar para o próprio objeto')
