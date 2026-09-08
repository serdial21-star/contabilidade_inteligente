'''Orquestra contratos operacionais sem mover regras dos domínios de origem.'''

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
from uuid import UUID

from serdial21.modules.access_control.application.services.authorization import (
    AuthorizationRequest, AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.banking.application.services.ofx_importer import (
    OfxImportRequest, OfxImportResult, OfxImportService,
)
from serdial21.modules.intake_documents.application.services.intake import (
    DocumentIntakeService, IntakeContext, StartBatchRequest,
)
from serdial21.modules.intake_documents.domain.entities import ImportBatch
from serdial21.modules.operations.application.ports.repository import OperationalQueryRepository
from serdial21.modules.workflow.application.journey import Journey, JourneyCommand
from serdial21.modules.workflow.application.services.nfe_to_dominio import NFeToDominioService


class OperationalConflictError(RuntimeError):
    '''Conflito estável de idempotência ou concorrência.'''


class OperationalUnavailableError(LookupError):
    '''Ausente e fora do escopo são indistinguíveis.'''


@dataclass(frozen=True, slots=True)
class NFeImportCommand:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID
    idempotency_key: str
    accounting_date: date
    period_start: date
    period_end: date
    approval_expires_at: datetime
    content: bytes
    filename: str
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class OfxImportCommand:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID
    idempotency_key: str
    content: bytes
    filename: str
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class ProcessingView:
    id: UUID
    kind: str
    source: str
    status: str
    total_items: int
    received_items: int
    duplicate_items: int
    failed_items: int
    started_at: datetime | None
    completed_at: datetime | None
    revision: int


@dataclass(frozen=True, slots=True)
class ReviewSummary:
    journey_id: UUID
    version: int
    status: str
    revision_id: UUID
    revision_hash: str
    accounting_date: date
    request_id: UUID | None
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class ReviewLineView:
    account_version_id: UUID
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal


@dataclass(frozen=True, slots=True)
class ReviewDetail:
    summary: ReviewSummary
    proposer_id: UUID
    validation_status: str | None
    lines: tuple[ReviewLineView, ...]
    source_count: int


@dataclass(frozen=True, slots=True)
class ExceptionView:
    id: UUID
    transformation_run_id: UUID
    code: str
    severity: str
    field_path: str | None
    rule_reference: str | None
    resolution_status: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuditView:
    id: UUID
    actor_id: UUID | None
    origin: str
    module: str
    action: str
    subject_type: str
    subject_id: UUID
    subject_version: int | None
    correlation_id: UUID
    occurred_at: datetime
    integrity_valid: bool


class OperationalService:
    def __init__(
        self, repository: OperationalQueryRepository,
        authorization: AuthorizationService, intake: DocumentIntakeService,
        nfe: NFeToDominioService, ofx: OfxImportService, audit: AuditService,
    ) -> None:
        self._repository = repository
        self._authorization = authorization
        self._intake = intake
        self._nfe = nfe
        self._ofx = ofx
        self._audit = audit

    def import_nfe(self, command: NFeImportCommand) -> Journey:
        return self._nfe.prepare(JourneyCommand(
            command.tenant_id, command.company_id, command.actor_id,
            command.idempotency_key, command.accounting_date,
            command.period_start, command.period_end,
            command.approval_expires_at,
        ), content=command.content, filename=command.filename,
            correlation_id=command.correlation_id)

    def import_ofx(self, command: OfxImportCommand) -> OfxImportResult:
        context = IntakeContext(
            command.tenant_id, command.company_id, command.actor_id,
            AuditOrigin.HUMAN, command.correlation_id,
        )
        batch = self._intake.start_batch(
            context, StartBatchRequest('OFX_OPERATIONAL', command.idempotency_key),
        )
        existing_hash = self._repository.batch_content_hash(
            command.tenant_id, command.company_id, batch.id,
        )
        supplied_hash = sha256(command.content).hexdigest()
        if existing_hash is not None and existing_hash != supplied_hash:
            raise OperationalConflictError('idempotency content conflict')
        return self._ofx.import_ofx(context, OfxImportRequest(
            batch.id, command.content, command.filename,
            external_key=command.idempotency_key,
        ))

    def processing(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, batch_id: UUID,
    ) -> ProcessingView:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        batch = self._repository.get_batch(tenant_id, company_id, batch_id)
        if batch is not None:
            return _processing(batch)
        journey = self._repository.get_journey(tenant_id, company_id, batch_id)
        if journey is not None:
            return ProcessingView(
                journey.id, 'JOURNEY', 'NFE55', journey.status, 1, 1,
                1 if journey.imported.status == 'IDEMPOTENT_REDELIVERY' else 0,
                1 if journey.status == 'QUARANTINED' else 0,
                None, None, journey.version,
            )
        raise OperationalUnavailableError()

    def reviews(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *, limit: int,
    ) -> tuple[ReviewSummary, ...]:
        self._require(tenant_id, company_id, actor_id, 'journal.read')
        return tuple(
            summary for journey in self._repository.list_journeys(
                tenant_id, company_id, limit=limit,
            ) if (summary := _review_summary(journey)) is not None
        )

    def review(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, journey_id: UUID,
    ) -> ReviewDetail:
        self._require(tenant_id, company_id, actor_id, 'journal.read')
        journey = self._repository.get_journey(tenant_id, company_id, journey_id)
        if journey is None:
            raise OperationalUnavailableError()
        summary = _review_summary(journey)
        if summary is None or journey.plan is None:
            raise OperationalUnavailableError()
        accounts = {item.id: item for item in journey.plan.accounts}
        lines = tuple(ReviewLineView(
            line.account_version_id,
            accounts[line.account_version_id].code,
            accounts[line.account_version_id].name,
            line.debit, line.credit,
        ) for line in journey.lines)
        return ReviewDetail(
            summary, journey.proposer_id, journey.validation_status,
            lines, len(journey.sources),
        )

    def decide(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        correlation_id: UUID, journey_id: UUID, *, expected_version: int,
        revision_id: UUID, revision_hash: str, decision: str,
        idempotency_key: str,
    ) -> Journey:
        return self._nfe.record_decision(IntakeContext(
            tenant_id, company_id, actor_id, AuditOrigin.HUMAN, correlation_id,
        ), journey_id, expected_version=expected_version,
            revision_id=revision_id, revision_hash=revision_hash,
            decision=decision, idempotency_key=idempotency_key)

    def exceptions(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *, limit: int,
    ) -> tuple[ExceptionView, ...]:
        self._require(tenant_id, company_id, actor_id, 'company.read')
        return tuple(ExceptionView(
            item.id, item.transformation_run_id, item.code, item.severity,
            item.field_path, item.rule_reference, item.resolution_status,
            item.created_at,
        ) for item in self._repository.list_issues(
            tenant_id, company_id, limit=limit,
        ))

    def audit_events(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, *, limit: int,
    ) -> tuple[AuditView, ...]:
        self._require(tenant_id, company_id, actor_id, 'audit.read')
        return tuple(AuditView(
            item.id, item.actor_id, item.origin.value, item.module, item.action,
            item.subject_type, item.subject_id, item.subject_version,
            item.correlation_id, item.occurred_at,
            self._audit.verify_integrity(item),
        ) for item in self._repository.list_audit_events(
            tenant_id, company_id, limit=limit,
        ))

    def _require(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, permission: str,
    ) -> None:
        self._authorization.require(AuthorizationRequest(
            tenant_id, actor_id, PermissionCode(permission), company_id,
        ))


def _processing(batch: ImportBatch) -> ProcessingView:
    return ProcessingView(
        batch.id, 'BATCH', batch.source, batch.status, batch.total_items,
        batch.received_items, batch.duplicate_items, batch.failed_items,
        batch.started_at, batch.completed_at, batch.revision,
    )


def _review_summary(journey: Journey) -> ReviewSummary | None:
    if journey.revision is None or journey.revision_hash is None:
        return None
    return ReviewSummary(
        journey.id, journey.version, journey.status, journey.revision.id,
        journey.revision_hash, journey.revision.accounting_date,
        journey.request.id if journey.request else None,
        journey.request.expires_at if journey.request else None,
    )
