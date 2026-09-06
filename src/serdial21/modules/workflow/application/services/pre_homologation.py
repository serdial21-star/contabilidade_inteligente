"""Orquestra a intenção de exportação sem produzir arquivo ou efeito contábil."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.models import FiscalDocumentModel
from serdial21.modules.workflow.adapters.outbound.persistence.models import (
    ApprovalRequestModel, AuthorizedEffectModel, PreHomologationExportBatchModel,
    WorkflowCaseModel, WorkItemModel,
)


BLOCK_REASONS = (
    'DOMINIO_CONNECTOR_NOT_HOMOLOGATED',
    'DOMINIO_GOLDEN_FILE_MISSING',
    'DOMINIO_LAYOUT_VERSION_UNKNOWN',
)


class JourneyResourceUnavailableError(RuntimeError):
    """Não revela a existência de recursos de outro escopo."""


@dataclass(frozen=True, slots=True)
class PreHomologationContext:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID | None
    correlation_id: UUID
    origin: AuditOrigin


@dataclass(frozen=True, slots=True)
class PreHomologationJourney:
    workflow_case_id: UUID
    work_item_id: UUID
    approval_request_id: UUID
    authorized_effect_id: UUID
    export_batch_id: UUID
    status: str
    block_reasons: tuple[str, ...]


class PreHomologationJourneyService:
    """Cria somente a fila humana e a intenção bloqueada para o Domínio.

    A ausência de regra publicada e de aprovação humana permanece explícita:
    não há proposta, revisão, decisão, payload autorizado nem serialização.
    """

    def __init__(self, session: Session, audit: AuditService, *,
                 id_factory: Callable[[], UUID] = uuid4,
                 clock: Callable[[], datetime] | None = None) -> None:
        self._session = session
        self._audit = audit
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_blocked_intent(
        self, context: PreHomologationContext, *, fiscal_document_id: UUID,
    ) -> PreHomologationJourney:
        document = self._session.scalar(select(FiscalDocumentModel).where(
            FiscalDocumentModel.id == fiscal_document_id,
            FiscalDocumentModel.tenant_id == context.tenant_id,
            FiscalDocumentModel.company_id == context.company_id,
        ))
        if document is None:
            raise JourneyResourceUnavailableError('resource unavailable')
        now = self._now()
        case = WorkflowCaseModel(
            id=self._id_factory(), tenant_id=context.tenant_id, company_id=context.company_id,
            subject_type='FiscalDocument', subject_id=document.id, status='PENDING_RULE',
            correlation_id=context.correlation_id, created_at=now,
        )
        item = WorkItemModel(
            id=self._id_factory(), tenant_id=context.tenant_id, company_id=context.company_id,
            workflow_case_id=case.id, subject_type='FiscalDocument', subject_id=document.id,
            work_type='RULE_EVALUATION_REQUIRED', status='OPEN', priority='NORMAL',
            assigned_to_membership_id=None, due_at=None, created_at=now, completed_at=None,
            correlation_id=context.correlation_id,
        )
        request = ApprovalRequestModel(
            id=self._id_factory(), tenant_id=context.tenant_id, company_id=context.company_id,
            workflow_case_id=case.id, proposal_revision_id=None, proposal_revision_hash=None,
            status='PENDING', requested_role='CONTADOR', correlation_id=context.correlation_id,
            created_at=now,
        )
        effect = AuthorizedEffectModel(
            id=self._id_factory(), tenant_id=context.tenant_id, company_id=context.company_id,
            workflow_case_id=case.id, approval_request_id=request.id,
            subject_type='FiscalDocument', subject_id=document.id,
            effect_type='DOMINIO_EXPORT',
            requested_payload={'fiscal_document_id': str(document.id)},
            authorized_payload=None, authorization_status='PENDING',
            authorized_by_membership_id=None, authorized_at=None, executed_at=None,
            execution_status='NOT_EXECUTED', correlation_id=context.correlation_id,
            created_at=now,
        )
        batch = PreHomologationExportBatchModel(
            id=self._id_factory(), tenant_id=context.tenant_id, company_id=context.company_id,
            authorized_effect_id=effect.id, fiscal_document_id=document.id,
            canonical_record_id=document.canonical_record_id, artifact_id=document.artifact_id,
            connector_name='DOMINIO', status='BLOCKED_FOR_HOMOLOGATION',
            block_reasons=list(BLOCK_REASONS), correlation_id=context.correlation_id,
            created_at=now,
        )
        for model in (case, item, request, effect, batch):
            self._session.add(model)
            self._session.flush()
        self._record(context, 'workflow_case.created', 'WorkflowCase', case.id,
                     {'status': case.status, 'subject_type': case.subject_type})
        self._record(context, 'work_item.created', 'WorkItem', item.id,
                     {'status': item.status, 'work_type': item.work_type})
        self._record(context, 'approval_request.pending', 'ApprovalRequest', request.id,
                     {'status': request.status, 'requested_role': request.requested_role})
        self._record(context, 'authorized_effect.pending', 'AuthorizedEffect', effect.id,
                     {'approval_status': effect.authorization_status, 'execution_status': effect.execution_status})
        self._record(context, 'export_batch.blocked_for_homologation', 'ExportBatch', batch.id,
                     {'status': batch.status, 'block_reasons': list(BLOCK_REASONS)})
        return PreHomologationJourney(case.id, item.id, request.id, effect.id, batch.id,
                                      batch.status, BLOCK_REASONS)

    def _record(self, context: PreHomologationContext, action: str, subject_type: str,
                subject_id: UUID, after: dict[str, object]) -> None:
        self._audit.record(AuditRecord(
            tenant_id=context.tenant_id, company_id=context.company_id, actor_id=context.actor_id,
            origin=context.origin, module='workflow', action=action, subject_type=subject_type,
            subject_id=subject_id, subject_version=1, before=None, after=after, reason=None,
            correlation_id=context.correlation_id,
        ))

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError('relógio deve retornar datetime com timezone')
        return now.astimezone(UTC)
