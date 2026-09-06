'''Identidades imutáveis para efeitos críticos e processamento retomável.'''

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class IdempotencyStatus(StrEnum):
    COMPLETED = 'COMPLETED'
    CONFLICT = 'CONFLICT'


class OutboxStatus(StrEnum):
    PENDING = 'PENDING'
    PUBLISHED = 'PUBLISHED'


class JobStatus(StrEnum):
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    BLOCKED = 'BLOCKED'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class CriticalOperation(StrEnum):
    IMPORT = 'IMPORT'
    PROPOSAL = 'PROPOSAL'
    JOURNAL = 'JOURNAL'
    APPROVAL = 'APPROVAL'
    EXPORT = 'EXPORT'


class IdempotencyConflictError(ValueError):
    code = 'CONFLICT'

    def __init__(self) -> None:
        super().__init__('idempotency key reused with different content')


class JobRevalidationError(PermissionError):
    code = 'job_revalidation_failed'

    def __init__(self) -> None:
        super().__init__('processing job is no longer valid for effect')


@dataclass(frozen=True, slots=True)
class DomainEvent:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    event_type: str
    schema_version: str
    subject_type: str
    subject_id: UUID
    payload_hash: str
    correlation_id: UUID
    causation_id: UUID | None
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    event_id: UUID
    payload_hash: str
    status: OutboxStatus
    attempt_count: int


@dataclass(frozen=True, slots=True)
class InboxReceipt:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    consumer: str
    idempotency_key: str
    payload_hash: str
    result_id: UUID
    status: IdempotencyStatus


@dataclass(frozen=True, slots=True)
class ProcessingJob:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    operation: CriticalOperation
    subject_id: UUID
    required_permission: str
    expected_version: int
    expected_status: str
    status: JobStatus
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class JobEffectState:
    '''Snapshot obtido imediatamente antes do commit do efeito final.'''

    tenant_id: UUID
    company_id: UUID
    version: int
    status: str
    permission_granted: bool
    unlocked: bool


def revalidate_job(job: ProcessingJob, state: JobEffectState) -> None:
    if (job.tenant_id, job.company_id) != (state.tenant_id, state.company_id):
        raise JobRevalidationError()
    if not state.permission_granted or not state.unlocked:
        raise JobRevalidationError()
    if job.expected_version != state.version or job.expected_status != state.status:
        raise JobRevalidationError()
    if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
        raise JobRevalidationError()
