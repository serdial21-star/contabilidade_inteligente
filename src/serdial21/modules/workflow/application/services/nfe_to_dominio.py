"""Orquestra NF-e até o gate real do Domínio, sem decidir pelo usuário.

Todos os métodos usam a UoW do chamador: commit só após retorno e rollback
obrigatório em exceções. Nenhuma chamada de fornecedor ocorre aqui.
"""
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from uuid import UUID, uuid4

from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError, AuthorizationRequest, AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.accounting.domain.entities import (
    AccountingProposal, JournalEntryRevision, JournalLine, JournalEntrySourceLink, validate_revision,
)
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.fiscal_documents.application.ports.repository import FiscalDocumentRepository
from serdial21.modules.fiscal_documents.application.services.nfe55_importer import NFe55ImportRequest, NFe55ImportService
from serdial21.modules.integrations.application.ports.connector import ConnectorPort, ConnectorConfiguration, LayoutSpecificationRequiredError
from serdial21.modules.integrations.domain.entities import ExportBatch
from serdial21.modules.intake_documents.application.services.intake import DocumentIntakeService, IntakeContext, StartBatchRequest
from serdial21.modules.locks.domain.entities import (
    EffectChannel, EffectContext, EffectOperation, validate_effect,
)
from serdial21.modules.rules.domain.entities import evaluate
from serdial21.modules.workflow.application.journey import (
    Journey, JourneyCatalog, JourneyCommand, JourneyConflictError,
    JourneyNotReadyError, JourneyRepository, JourneyUnavailableError,
)
from serdial21.modules.workflow.domain.entities import (
    ApprovalRequest, ApprovalStep, AuthorizedEffect, WorkflowCase,
    WorkItem, WorkItemSubject, decide,
)
from serdial21.shared_kernel.observability import MetricsRegistry, processing_started


def digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def revision_digest(journey: Journey) -> str:
    if journey.revision is None:
        raise JourneyNotReadyError('revision required')
    # A transição de estado não muda o conteúdo aprovado.
    revision = replace(journey.revision, status='DRAFT')
    return digest({
        'revision': asdict(revision), 'lines': [asdict(line) for line in journey.lines],
        'sources': [asdict(source) for source in journey.sources],
        'source_hash': journey.imported.content_hash,
        'plan': asdict(journey.plan) if journey.plan else None,
        'evaluation': asdict(journey.evaluation) if journey.evaluation else None,
        'proposal': asdict(journey.proposal) if journey.proposal else None,
    })


class NFeToDominioService:
    def __init__(
        self, repository: JourneyRepository, catalog: JourneyCatalog,
        authorization: AuthorizationService, intake: DocumentIntakeService,
        importer: NFe55ImportService, fiscal: FiscalDocumentRepository,
        audit: AuditService, connector: ConnectorPort,
        *, clock: Callable[[], datetime] | None = None,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self._repository = repository
        self._catalog = catalog
        self._authorization = authorization
        self._intake = intake
        self._importer = importer
        self._fiscal = fiscal
        self._audit = audit
        self._connector = connector
        self._clock = clock or (lambda: datetime.now(UTC))
        self._metrics = metrics or MetricsRegistry()

    def prepare(
        self, command: JourneyCommand, *, content: bytes, filename: str,
        correlation_id: UUID | None = None,
    ) -> Journey:
        """Importa e prepara; jamais toma uma decisão de aprovação."""
        started = processing_started()
        now = self._now()
        self._require(command.tenant_id, command.company_id, command.actor_id, 'journal.propose')
        if not command.idempotency_key.strip() or len(command.idempotency_key) > 128:
            raise ValueError('invalid idempotency key')
        if command.approval_expires_at.tzinfo is None:
            raise ValueError('approval expiry requires timezone')
        command_hash = digest({'command': asdict(command), 'source_hash': sha256(content).hexdigest()})
        existing = self._repository.find_by_key(command.tenant_id, command.company_id, command.idempotency_key)
        if existing is not None:
            if existing.command_hash != command_hash:
                raise JourneyConflictError('idempotency content conflict')
            self._metrics.increment('retries_total')
            return self._completed(existing, started)
        if command.approval_expires_at <= now:
            raise JourneyNotReadyError('approval expiry must be in the future')
        if not command.period_start <= command.accounting_date <= command.period_end:
            raise JourneyNotReadyError('invalid accounting period')
        correlation_id = correlation_id or uuid4()
        context = IntakeContext(command.tenant_id, command.company_id, command.actor_id, AuditOrigin.HUMAN, correlation_id)
        batch = self._intake.start_batch(context, StartBatchRequest('NFE55_VERTICAL', command.idempotency_key))
        imported = self._importer.import_xml(context, NFe55ImportRequest(batch.id, content, filename))
        journey = Journey(
            uuid4(), command.tenant_id, command.company_id, correlation_id,
            command.idempotency_key, command_hash, 1, 'IMPORTED', command.actor_id, imported,
        )
        if imported.status not in {'IMPORTED', 'IDEMPOTENT_REDELIVERY'}:
            return self._completed(
                self._save(replace(journey, status='QUARANTINED'), command.actor_id, 'journey.quarantined'),
                started,
            )
        self._save(journey, command.actor_id, 'journey.imported')
        plan = self._catalog.preparation(
            command.tenant_id, command.company_id, command.accounting_date,
        )
        if plan is None:
            return self._completed(
                self._save(journey.advance(status='PENDING_RULE'), command.actor_id, 'journey.pending_rule'),
                started,
            )
        scope = (command.tenant_id, command.company_id)
        if any((obj.tenant_id, obj.company_id) != scope for obj in (
            plan.release, plan.ledger, plan.posting, *plan.accounts, *plan.rules,
        )):
            raise JourneyUnavailableError()
        if (plan.release.status, plan.posting.status, plan.workflow.status) != ('PUBLISHED',) * 3:
            raise JourneyNotReadyError('published preparation versions required')
        if plan.ledger.status != 'ACTIVE' or not plan.ledger.valid_from <= command.accounting_date:
            raise JourneyNotReadyError('ledger unavailable')
        if plan.ledger.valid_to is not None and command.accounting_date > plan.ledger.valid_to:
            raise JourneyNotReadyError('ledger expired')
        if plan.posting.amount_field != 'invoice_total' or not 0 <= plan.posting.decimal_places <= 6:
            raise JourneyNotReadyError('unsupported explicit posting policy')
        pair = self._fiscal.find_by_access_key(command.tenant_id, command.company_id, imported.access_key or '')
        if pair is None:
            raise JourneyUnavailableError()
        document, canonical = pair
        if document.id != imported.fiscal_document_id or canonical.id != imported.canonical_record_id:
            raise JourneyConflictError('canonical source mismatch')
        inputs = {
            'model': document.model, 'operation_nature': document.operation_nature,
            'invoice_total': str(document.invoice_total), 'source_hash': canonical.source_hash,
            'canonical_fingerprint': canonical.fingerprint, 'schema_version': canonical.schema_version,
        }
        evaluation = evaluate(plan.release, plan.rules, inputs, command.accounting_date)
        journey = self._save(journey.advance(plan=plan, evaluation=evaluation, status='EVALUATED'),
                             command.actor_id, 'rule_evaluation.completed')
        if evaluation.proposal is None:
            return self._completed(
                self._save(journey.advance(status='PENDING_RULE'), command.actor_id, 'journey.pending_rule'),
                started,
            )
        amount = document.invoice_total
        quantum = Decimal(1).scaleb(-plan.posting.decimal_places)
        if not amount.is_finite() or amount <= 0 or amount != amount.quantize(quantum):
            raise JourneyNotReadyError('amount requires an explicit accounting decision')
        proposal = AccountingProposal(uuid4(), *scope, 'RuleEvaluation', evaluation.id, 'PROPOSED')
        journey = self._save(journey.advance(proposal=proposal, status='PROPOSED'), command.actor_id, 'accounting_proposal.created')
        revision = JournalEntryRevision(
            uuid4(), *scope, plan.ledger.id, uuid4(), 1, command.accounting_date,
            command.period_start, command.period_end, 'DRAFT', None,
        )
        lines = tuple(JournalLine(
            uuid4(), *scope, plan.ledger.id, revision.id,
            UUID(evaluation.proposal[f'{side}_account_version_id']),
            amount if side == 'debit' else Decimal(0), amount if side == 'credit' else Decimal(0),
        ) for side in ('debit', 'credit'))
        sources = (JournalEntrySourceLink(uuid4(), *scope, revision.entry_id, 'FiscalDocument', document.id, 'ORIGIN'),)
        journey = self._save(journey.advance(revision=revision, lines=lines, sources=sources, status='DRAFT'),
                             command.actor_id, 'journal_revision.created')
        self._validate(journey)
        self._check_locks(journey, EffectOperation.ALTER)
        journey = replace(journey, revision_hash=revision_digest(journey))
        journey = self._save(journey.advance(validation_status='VALID', status='VALIDATED'),
                             command.actor_id, 'journal_revision.validated')
        case = WorkflowCase(uuid4(), *scope, plan.workflow.id, revision.id, 'OPEN')
        item = WorkItem(uuid4(), case.id, 'OPEN', plan.responsible_role)
        subject = WorkItemSubject(uuid4(), item.id, 'JournalEntryRevision', revision.id, journey.revision_hash)
        journey = self._save(journey.advance(case=case, item=item, subject=subject, status='IN_REVIEW'),
                             command.actor_id, 'work_item.created')
        request = ApprovalRequest(
            uuid4(), *scope, case.id, revision.id, journey.revision_hash, 'PENDING',
            command.approval_expires_at, True, command.actor_id,
        )
        step = ApprovalStep(uuid4(), request.id, 1, plan.approval_role, 'PENDING')
        return self._completed(
            self._save(journey.advance(request=request, step=step, status='PENDING_APPROVAL'),
                       command.actor_id, 'approval_request.created'),
            started,
        )

    def record_decision(
        self, context: IntakeContext, journey_id: UUID, *, expected_version: int,
        revision_id: UUID, revision_hash: str, decision: str,
    ) -> Journey:
        """Comando humano autenticado, vinculado à revisão vista pelo Contador."""
        self._human(context)
        self._require(
            context.tenant_id, context.company_id, context.actor_id,
            'journal.approve',
        )
        journey = self._get(context, journey_id)
        if journey.plan is None:
            raise JourneyNotReadyError('published workflow required')
        self._require(
            context.tenant_id, context.company_id, context.actor_id,
            'journal.approve', role_name=journey.plan.approval_role,
        )
        self._expected(journey, expected_version)
        if journey.status != 'PENDING_APPROVAL' or journey.request is None or journey.step is None or journey.revision is None:
            raise JourneyNotReadyError('pending approval required')
        if revision_id != journey.revision.id or revision_hash != revision_digest(journey):
            raise JourneyConflictError('revision mismatch')
        self._validate(journey)
        self._check_locks(journey, EffectOperation.APPROVE)
        result = decide(journey.request, journey.step, context.actor_id, revision_hash, self._now(),
                        authorized=True, existing=(), decision=decision)
        journey = self._save(journey.advance(
            decision=result, request=replace(journey.request, status=decision),
            step=replace(journey.step, status=decision),
            item=replace(journey.item, status='COMPLETED'),
            status=decision, revision=(journey.revision.approve() if decision == 'APPROVED'
                                      else replace(journey.revision, status='REJECTED')),
        ), context.actor_id, 'approval_decision.recorded')
        if decision == 'REJECTED':
            return journey
        effect = AuthorizedEffect(uuid4(), journey.request.id, result.id, 'DOMINIO_EXPORT', 'AUTHORIZED')
        return self._save(journey.advance(effect=effect), context.actor_id, 'authorized_effect.created')

    def request_export(
        self, context: IntakeContext, journey_id: UUID, *, expected_version: int,
        route_id: UUID, configuration: ConnectorConfiguration,
    ) -> Journey:
        """Cria lote após aprovação válida e consulta o conector real.

        Nesta execução o Domínio recusa a configuração. Um conector que passe
        esse gate também não é entregue automaticamente: exige implementação
        homologada da preparação/arquivo e seu protocolo transacional.
        """
        self._human(context)
        self._require(context.tenant_id, context.company_id, context.actor_id, 'export.execute')
        journey = self._get(context, journey_id)
        self._expected(journey, expected_version)
        self._exportable(journey)
        self._check_locks(journey, EffectOperation.EXPORT)
        if journey.batch is not None:
            if journey.batch.route_id != route_id or journey.connector_configuration != configuration:
                raise JourneyConflictError('export content conflict')
            self._metrics.increment('retries_total')
            return journey
        batch = ExportBatch(uuid4(), journey.tenant_id, journey.company_id, route_id, 'PREPARING')
        journey = self._save(journey.advance(batch=batch, connector_configuration=configuration),
                             context.actor_id, 'export_batch.created')
        try:
            self._connector.validate_configuration(configuration)
        except LayoutSpecificationRequiredError:
            return self._save(journey.advance(
                status='BLOCKED_FOR_HOMOLOGATION', batch=replace(batch, status='BLOCKED_FOR_HOMOLOGATION'),
            ), context.actor_id, 'export_batch.blocked_for_homologation')
        raise JourneyNotReadyError('homologated file preparation is not implemented')

    def supersede(self, context: IntakeContext, journey_id: UUID, *, expected_version: int) -> Journey:
        self._human(context)
        self._require(context.tenant_id, context.company_id, context.actor_id, 'journal.propose')
        journey = self._get(context, journey_id)
        self._expected(journey, expected_version)
        if journey.revision is None or journey.status in {'SUPERSEDED', 'REJECTED'}:
            raise JourneyNotReadyError('revision cannot be superseded')
        self._check_locks(journey, EffectOperation.ALTER)
        return self._save(journey.advance(
            status='SUPERSEDED', revision=replace(journey.revision, status='SUPERSEDED'),
            request=replace(journey.request, status='INVALIDATED') if journey.request else None,
            effect=replace(journey.effect, status='INVALIDATED') if journey.effect else None,
            batch=replace(journey.batch, status='CANCELLED') if journey.batch else None,
        ), context.actor_id, 'journal_revision.superseded')

    def trace_export(self, context: IntakeContext, batch_id: UUID) -> tuple[Journey, bytes]:
        self._require(context.tenant_id, context.company_id, context.actor_id, 'journal.read')
        journey = self._repository.find_by_export(context.tenant_id, context.company_id, batch_id)
        if journey is None:
            raise JourneyUnavailableError()
        content = self._intake.read_evidence(
            replace(context, correlation_id=journey.correlation_id), journey.imported.artifact_id,
        )
        if sha256(content).hexdigest() != journey.imported.content_hash:
            raise JourneyConflictError('source integrity mismatch')
        return journey, content

    def _exportable(self, journey: Journey) -> None:
        if (journey.status not in {'APPROVED', 'BLOCKED_FOR_HOMOLOGATION'}
            or journey.revision is None or journey.revision.status != 'APPROVED_INTERNAL'
            or journey.request is None or journey.request.status != 'APPROVED'
            or journey.decision is None or journey.decision.decision != 'APPROVED'
            or journey.effect is None or journey.effect.status != 'AUTHORIZED'
            or journey.validation_status != 'VALID'):
            raise JourneyNotReadyError('valid human approval required')
        if (journey.decision.request_id != journey.request.id
            or journey.effect.request_id != journey.request.id
            or journey.effect.decision_id != journey.decision.id
            or journey.request.revision_id != journey.revision.id
            or journey.request.revision_hash != revision_digest(journey)
            or journey.decision.revision_hash != journey.request.revision_hash):
            raise JourneyConflictError('approval content mismatch')
        # Aprovação antiga não transforma membership/CompanyAccess revogado em autoridade.
        self._require(journey.tenant_id, journey.company_id, journey.decision.actor_id,
                      'journal.approve', role_name='CONTADOR')
        if self._now() >= journey.request.expires_at:
            raise JourneyNotReadyError('approval expired')
        self._validate(journey)

    def _validate(self, journey: Journey) -> None:
        if journey.revision is None or journey.plan is None:
            raise JourneyNotReadyError('revision required')
        validate_revision(journey.revision, journey.lines, journey.plan.accounts, journey.sources)
        for line in journey.lines:
            account = next(a for a in journey.plan.accounts if a.id == line.account_version_id)
            account.validate()
            if account.valid_from > journey.revision.accounting_date or (
                account.valid_to is not None and account.valid_to < journey.revision.accounting_date
            ):
                raise JourneyNotReadyError('account outside validity')

    def _check_locks(self, journey: Journey, operation: EffectOperation) -> None:
        if journey.revision is None or journey.plan is None:
            raise JourneyNotReadyError('revision required')
        locks = self._catalog.locks(journey.tenant_id, journey.company_id)
        groups = dict(journey.plan.account_groups)
        for line in journey.lines:
            account = next(a for a in journey.plan.accounts if a.id == line.account_version_id)
            if account.account_id not in groups:
                raise JourneyNotReadyError('account hierarchy unavailable')
            result = validate_effect(locks, EffectContext(
                journey.tenant_id, journey.company_id, account.account_id, groups[account.account_id],
                'accounting', journey.revision.accounting_date, operation, EffectChannel.USER,
            ))
            if result.reconciliation_requires_review:
                raise JourneyNotReadyError('released lock requires a new review')

    def _require(self, tenant_id: UUID, company_id: UUID, actor_id: UUID | None,
                 permission: str, *, role_name: str | None = None) -> None:
        if actor_id is None:
            raise AccessDeniedError()
        self._authorization.require(AuthorizationRequest(
            tenant_id, actor_id, PermissionCode(permission), company_id,
        ), at=self._now(), role_name=role_name)

    @staticmethod
    def _human(context: IntakeContext) -> None:
        if context.origin != AuditOrigin.HUMAN or context.actor_id is None:
            raise AccessDeniedError()

    def _get(self, context: IntakeContext, journey_id: UUID) -> Journey:
        journey = self._repository.get(context.tenant_id, context.company_id, journey_id)
        if journey is None:
            raise JourneyUnavailableError()
        return journey

    @staticmethod
    def _expected(journey: Journey, expected: int) -> None:
        if journey.version != expected:
            raise JourneyConflictError('stale journey version')

    def _save(self, journey: Journey, actor_id: UUID, action: str) -> Journey:
        self._repository.append(journey)
        self._audit.record(AuditRecord(
            tenant_id=journey.tenant_id, company_id=journey.company_id, actor_id=actor_id,
            origin=AuditOrigin.HUMAN, module='workflow', action=action, subject_type='NFeJourney',
            subject_id=journey.id, subject_version=journey.version, before=None,
            after={'status': journey.status, 'revision_hash': journey.revision_hash,
                   'evaluation_id': journey.evaluation.id if journey.evaluation else None,
                   'proposal_id': journey.proposal.id if journey.proposal else None,
                   'revision_id': journey.revision.id if journey.revision else None,
                   'work_item_id': journey.item.id if journey.item else None,
                   'request_id': journey.request.id if journey.request else None,
                   'decision_id': journey.decision.id if journey.decision else None,
                   'effect_id': journey.effect.id if journey.effect else None,
                   'export_batch_id': journey.batch.id if journey.batch else None},
            reason=None, correlation_id=journey.correlation_id,
        ))
        self._record_metric(action, journey.status)
        return journey

    def _record_metric(self, action: str, status: str) -> None:
        if action == 'journey.imported':
            self._metrics.increment('imports_total')
        elif action == 'journey.quarantined':
            self._metrics.increment('imports_total')
            self._metrics.increment('errors_total')
        elif action == 'accounting_proposal.created':
            self._metrics.increment('proposals_total')
        elif action == 'approval_decision.recorded':
            self._metrics.increment(
                'approvals_total' if status == 'APPROVED' else 'rejections_total',
            )
        elif action in {'journey.pending_rule', 'approval_request.created'}:
            self._metrics.increment('pending_total')
        elif action == 'export_batch.created':
            self._metrics.increment('exports_total')

    def _completed(self, journey: Journey, started: float) -> Journey:
        self._metrics.observe_processing(processing_started() - started)
        return journey

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError('clock requires timezone')
        return now.astimezone(UTC)

