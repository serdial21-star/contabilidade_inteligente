from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4


class ApprovalStatus(StrEnum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'


class HoldStatus(StrEnum):
    ACTIVE = 'ACTIVE'
    RELEASED = 'RELEASED'


class RetentionDecision(StrEnum):
    KEEP = 'KEEP'
    LEGAL_HOLD = 'LEGAL_HOLD'
    PENDING_POLICY_APPROVAL = 'PENDING_POLICY_APPROVAL'
    ELIGIBLE_FOR_RETENTION_ACTION = 'ELIGIBLE_FOR_RETENTION_ACTION'
    NOT_APPLICABLE = 'NOT_APPLICABLE'


class DsrStatus(StrEnum):
    RECEIVED = 'RECEIVED'
    IDENTITY_PENDING = 'IDENTITY_PENDING'
    IN_REVIEW = 'IN_REVIEW'
    COMPLETED = 'COMPLETED'
    DENIED = 'DENIED'


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    id: UUID; tenant_id: UUID; data_category: str; retention_days: int | None
    retention_trigger: str; legal_basis_status: str; destruction_mode: str
    approval_status: ApprovalStatus; exceptions: str | None; legal_hold_applicable: bool


@dataclass(frozen=True, slots=True)
class LegalHold:
    id: UUID; tenant_id: UUID; company_id: UUID | None; resource_type: str
    resource_id: UUID | None; reason_reference: str; status: HoldStatus
    created_at: datetime; created_by: UUID; released_at: datetime | None = None
    released_by: UUID | None = None

    def release(self, actor_id: UUID, at: datetime) -> 'LegalHold':
        if self.status is not HoldStatus.ACTIVE:
            raise ValueError('legal hold is not active')
        return replace(self, status=HoldStatus.RELEASED, released_at=at, released_by=actor_id)


@dataclass(frozen=True, slots=True)
class RetentionCandidate:
    tenant_id: UUID; company_id: UUID | None; resource_type: str; resource_id: UUID
    data_category: str; occurred_at: datetime


@dataclass(frozen=True, slots=True)
class RetentionEvaluation:
    candidate: RetentionCandidate; policy_id: UUID | None; decision: RetentionDecision; reason: str


@dataclass(frozen=True, slots=True)
class DataSubjectRequest:
    id: UUID; tenant_id: UUID; company_id: UUID | None; subject_reference_hash: str
    status: DsrStatus; created_at: datetime; created_by: UUID; verified_by: UUID | None = None
    completed_at: datetime | None = None

    def verify_identity(self, actor_id: UUID) -> 'DataSubjectRequest':
        if self.status is not DsrStatus.IDENTITY_PENDING:
            raise ValueError('identity verification is not pending')
        return replace(self, status=DsrStatus.IN_REVIEW, verified_by=actor_id)

    def complete(self, at: datetime) -> 'DataSubjectRequest':
        if self.status is not DsrStatus.IN_REVIEW:
            raise ValueError('identity verification is required before completion')
        return replace(self, status=DsrStatus.COMPLETED, completed_at=at)


def due(policy: RetentionPolicy, candidate: RetentionCandidate, now: datetime) -> bool:
    return policy.retention_days is not None and now >= candidate.occurred_at + timedelta(days=policy.retention_days)


def new_hold(tenant_id: UUID, company_id: UUID | None, resource_type: str, resource_id: UUID | None,
             reason_reference: str, actor_id: UUID, at: datetime) -> LegalHold:
    if not resource_type.strip() or not reason_reference.strip(): raise ValueError('hold requires scope and reference')
    return LegalHold(uuid4(), tenant_id, company_id, resource_type, resource_id, reason_reference, HoldStatus.ACTIVE, at, actor_id)
