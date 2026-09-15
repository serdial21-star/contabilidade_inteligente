'''Projeção somente leitura da Linha da Decisão sobre evidências existentes.'''

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from serdial21.modules.access_control.application.services.authorization import (
    AuthorizationRequest, AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditEvent
from serdial21.modules.locks.domain.entities import (
    AccountLockedError, EffectChannel, EffectContext, EffectOperation,
    validate_effect,
)
from serdial21.modules.operations.application.ports.repository import (
    OperationalQueryRepository,
)
from serdial21.modules.workflow.application.journey import Journey


class DecisionLineUnavailableError(LookupError):
    '''Mantém ausente e fora do escopo indistinguíveis.'''


class DecisionLineRoot(StrEnum):
    DOCUMENT = 'DOCUMENT'
    FISCAL_DOCUMENT = 'FISCAL_DOCUMENT'
    BANK_STATEMENT = 'BANK_STATEMENT'
    ACCOUNTING_PROPOSAL = 'ACCOUNTING_PROPOSAL'
    REVIEW = 'REVIEW'


@dataclass(frozen=True, slots=True)
class DecisionLineEvent:
    sequence: int
    occurred_at: datetime
    category: str
    actor_kind: str
    actor_display_name: str
    title: str
    description: str
    evidence_kind: str
    integrity_valid: bool


@dataclass(frozen=True, slots=True)
class DecisionLine:
    root_type: str
    root_id: UUID
    root_title: str
    root_status: str
    completeness: str
    data_gaps: tuple[str, ...]
    events: tuple[DecisionLineEvent, ...]


@dataclass(frozen=True, slots=True)
class _Projection:
    category: str
    actor_kind: str
    title: str
    description: str


_AUTOMATED = 'AUTOMATED'
_PROFESSIONAL = 'PROFESSIONAL_ACTION'
_GOVERNANCE = 'SYSTEM_GOVERNANCE'

_EVENTS: dict[str, _Projection] = {
    'import_batch.created': _Projection('RECEIPT', _PROFESSIONAL, 'Importação iniciada', 'O recebimento foi iniciado por ação profissional.'),
    'evidence_artifact.created': _Projection('SOURCE', _PROFESSIONAL, 'Evidência registrada', 'A evidência de origem foi preservada e identificada.'),
    'artifact_receipt.created': _Projection('RECEIPT', _PROFESSIONAL, 'Documento recebido', 'O documento foi recebido no contexto autorizado.'),
    'transformation_run.created': _Projection('PROCESSING', _AUTOMATED, 'Processamento executado', 'O conteúdo passou pelo processamento canônico registrado.'),
    'lineage_edge.created': _Projection('PROCESSING', _AUTOMATED, 'Linhagem vinculada', 'Uma relação determinística entre evidências foi registrada.'),
    'validation_issue.created': _Projection('VALIDATION', _AUTOMATED, 'Exceção de validação identificada', 'A validação registrou uma pendência para tratamento seguro.'),
    'nfe55.imported': _Projection('PROCESSING', _AUTOMATED, 'NF-e interpretada', 'A NF-e foi convertida para o modelo canônico.'),
    'ofx.imported': _Projection('PROCESSING', _AUTOMATED, 'Extrato OFX interpretado', 'O extrato e suas transações foram processados sem efeito contábil.'),
    'journey.imported': _Projection('PROCESSING', _AUTOMATED, 'Jornada iniciada', 'A evidência fiscal ingressou no fluxo determinístico.'),
    'journey.quarantined': _Projection('EXCEPTION', _GOVERNANCE, 'Documento em quarentena', 'O fluxo foi interrompido por validação segura.'),
    'rule_evaluation.completed': _Projection('RULE', _AUTOMATED, 'Regras avaliadas', 'O motor determinístico avaliou a versão aplicável.'),
    'journey.pending_rule': _Projection('EXCEPTION', _GOVERNANCE, 'Regra ausente ou ambígua', 'O fluxo parou com segurança e nenhuma proposta foi criada.'),
    'accounting_proposal.created': _Projection('PROPOSAL', _AUTOMATED, 'Proposta contábil criada', 'Uma sugestão determinística foi criada para revisão humana.'),
    'journal_revision.created': _Projection('PROPOSAL', _AUTOMATED, 'Revisão imutável criada', 'A revisão e sua identidade foram registradas.'),
    'journal_revision.validated': _Projection('VALIDATION', _AUTOMATED, 'Revisão validada', 'As invariantes contábeis da proposta foram verificadas.'),
    'work_item.created': _Projection('REVIEW', _GOVERNANCE, 'Revisão encaminhada', 'Um item foi disponibilizado à fila profissional; isto não comprova revisão realizada.'),
    'approval_request.created': _Projection('REVIEW', _GOVERNANCE, 'Decisão solicitada', 'A revisão exata foi submetida à decisão profissional.'),
    'authorized_effect.created': _Projection('APPROVAL', _GOVERNANCE, 'Efeito interno autorizado', 'A aprovação humana autorizou o próximo efeito interno; não representa escrituração oficial.'),
    'journal_revision.superseded': _Projection('EDIT', _PROFESSIONAL, 'Revisão substituída', 'Uma nova revisão tornou a anterior obsoleta.'),
    'account_lock.created': _Projection('BLOCK', _PROFESSIONAL, 'Bloqueio criado', 'Um bloqueio governado foi registrado.'),
    'account_lock.released': _Projection('UNBLOCK', _PROFESSIONAL, 'Bloqueio liberado', 'A liberação foi registrada sem retomada automática.'),
    'export_batch.blocked_for_homologation': _Projection('BLOCK', _GOVERNANCE, 'Exportação bloqueada', 'A exportação permanece bloqueada para homologação.'),
}


class DecisionLineService:
    def __init__(
        self, repository: OperationalQueryRepository,
        authorization: AuthorizationService, audit: AuditService,
    ) -> None:
        self._repository = repository
        self._authorization = authorization
        self._audit = audit

    def get(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID,
        root_type: DecisionLineRoot, root_id: UUID, *, limit: int,
    ) -> DecisionLine:
        if not 1 <= limit <= 100:
            raise ValueError('invalid trace limit')
        permission = 'journal.read' if root_type in {
            DecisionLineRoot.ACCOUNTING_PROPOSAL, DecisionLineRoot.REVIEW,
        } else 'company.read'
        self._require(tenant_id, company_id, actor_id, permission)
        self._require(tenant_id, company_id, actor_id, 'audit.read')

        title, status, references, correlations, journey = self._resolve_root(
            tenant_id, company_id, root_type, root_id,
        )
        if not correlations:
            correlations = self._repository.find_trace_correlation_ids(
                tenant_id, company_id, references, limit=8,
            )
        audit_events = self._repository.list_trace_audit_events(
            tenant_id, company_id, correlations, limit=limit,
        ) if correlations else ()
        actor_names = self._repository.actor_display_names(
            tenant_id,
            tuple({event.actor_id for event in audit_events if event.actor_id is not None}),
        )
        projected: list[tuple[datetime, str, DecisionLineEvent]] = []
        for event in audit_events:
            view = self._project(event, actor_names)
            if journey is not None:
                view = self._enrich_journey_event(
                    tenant_id, company_id, journey, event, view,
                )
            projected.append((event.occurred_at, str(event.id), view))

        gaps: list[str] = []
        if any(not item[2].integrity_valid for item in projected):
            gaps.append('AUDIT_INTEGRITY_NOT_CONFIRMED')
        if any(
            event.action not in _EVENTS and event.action != 'approval_decision.recorded'
            for event in audit_events
        ):
            gaps.append('UNMAPPED_AUDIT_ACTION')
        if journey is not None:
            projected.extend(self._active_lock_events(tenant_id, company_id, journey))
            if journey.item is not None:
                gaps.append('DISTINCT_REVIEW_ACTION_NOT_AVAILABLE')
            if journey.decision is not None and journey.decision.decision == 'REJECTED':
                gaps.append('REJECTION_REASON_NOT_AVAILABLE')
        if not audit_events:
            gaps.append('CORRELATED_AUDIT_NOT_AVAILABLE')

        projected.sort(key=lambda item: (item[0], item[1]))
        events = tuple(DecisionLineEvent(
            sequence=index, occurred_at=item.occurred_at,
            category=item.category, actor_kind=item.actor_kind,
            actor_display_name=item.actor_display_name, title=item.title,
            description=item.description, evidence_kind=item.evidence_kind,
            integrity_valid=item.integrity_valid,
        ) for index, (_, _, item) in enumerate(projected, 1))
        return DecisionLine(
            root_type.value, root_id, title, status,
            'PARTIAL' if gaps else 'COMPLETE', tuple(gaps), events,
        )

    def _resolve_root(
        self, tenant_id: UUID, company_id: UUID,
        root_type: DecisionLineRoot, root_id: UUID,
    ) -> tuple[str, str, tuple[tuple[str, UUID], ...], tuple[UUID, ...], Journey | None]:
        if root_type is DecisionLineRoot.DOCUMENT:
            row = self._repository.get_document(tenant_id, company_id, root_id)
            if row is None:
                raise DecisionLineUnavailableError()
            references = [
                ('ArtifactReceipt', row.id), ('EvidenceArtifact', row.artifact_id),
            ]
            fiscal_document_id = self._repository.linked_fiscal_document_id(
                tenant_id, company_id, row.artifact_id,
            )
            journey = None
            if fiscal_document_id is not None:
                references.append(('FiscalDocument', fiscal_document_id))
                journey = self._repository.get_journey_by_fiscal_document(
                    tenant_id, company_id, fiscal_document_id,
                )
            correlations = (journey.correlation_id,) if journey is not None else ()
            return (
                row.filename, row.processing_status, tuple(references), correlations,
                journey,
            )
        if root_type is DecisionLineRoot.FISCAL_DOCUMENT:
            row = self._repository.get_fiscal_document(tenant_id, company_id, root_id)
            if row is None:
                raise DecisionLineUnavailableError()
            refs = [('FiscalDocument', row.id), ('EvidenceArtifact', row.artifact_id)]
            if row.receipt_id is not None:
                refs.append(('ArtifactReceipt', row.receipt_id))
            journey = self._repository.get_journey_by_fiscal_document(
                tenant_id, company_id, row.id,
            )
            correlations = (journey.correlation_id,) if journey is not None else ()
            return (
                row.document_number or 'NF-e', row.observed_status, tuple(refs),
                correlations, journey,
            )
        if root_type is DecisionLineRoot.BANK_STATEMENT:
            row = self._repository.get_bank_statement(tenant_id, company_id, root_id)
            if row is None:
                raise DecisionLineUnavailableError()
            refs = [
                ('BankStatement', row.id), ('TransformationRun', row.transformation_run_id),
                ('EvidenceArtifact', row.artifact_id),
            ]
            if row.receipt_id is not None:
                refs.append(('ArtifactReceipt', row.receipt_id))
            return 'Extrato bancário', 'PROCESSED', tuple(refs), (), None
        journey = self._repository.get_journey(tenant_id, company_id, root_id)
        if journey is None or journey.proposal is None:
            raise DecisionLineUnavailableError()
        label = 'Revisão contábil' if root_type is DecisionLineRoot.REVIEW else 'Proposta contábil'
        return label, journey.status, (('Journey', journey.id),), (journey.correlation_id,), journey

    def _project(
        self, event: AuditEvent, actor_names: dict[UUID, str],
    ) -> DecisionLineEvent:
        integrity = self._audit.verify_integrity(event)
        if event.action == 'approval_decision.recorded':
            decision = str((event.after or {}).get('status', '')).upper()
            if decision not in {'APPROVED', 'REJECTED'}:
                projection = _Projection(
                    'EXCEPTION', _GOVERNANCE, 'Estado de decisão não reconhecido',
                    'A evidência foi preservada sem inferir aprovação ou rejeição.',
                )
            else:
                projection = _Projection(
                    'REJECTION' if decision == 'REJECTED' else 'APPROVAL',
                    _PROFESSIONAL,
                    'Proposta rejeitada' if decision == 'REJECTED' else 'Proposta aprovada',
                    'A decisão humana foi vinculada à revisão e ao hash exatos.',
                )
        else:
            projection = _EVENTS.get(event.action, _Projection(
                'EXCEPTION', _GOVERNANCE, 'Registro operacional correlacionado',
                'Existe evidência correlacionada sem apresentação detalhada neste contrato.',
            ))
        if projection.actor_kind == _PROFESSIONAL:
            actor_name = actor_names.get(event.actor_id, 'Profissional não identificado')
        elif projection.actor_kind == _AUTOMATED:
            actor_name = 'Automação'
        else:
            actor_name = 'Governança do sistema'
        if not integrity:
            return DecisionLineEvent(
                0, event.occurred_at, 'EXCEPTION', _GOVERNANCE,
                'Governança do sistema', 'Integridade não confirmada',
                'O conteúdo sem integridade válida não foi projetado.',
                'AUDIT_EVENT', False,
            )
        return DecisionLineEvent(
            0, event.occurred_at, projection.category, projection.actor_kind,
            actor_name, projection.title, projection.description,
            'AUDIT_EVENT', True,
        )

    def _enrich_journey_event(
        self, tenant_id: UUID, company_id: UUID, journey: Journey,
        event: AuditEvent, view: DecisionLineEvent,
    ) -> DecisionLineEvent:
        if not view.integrity_valid:
            return view
        if event.action == 'rule_evaluation.completed' and journey.evaluation is not None:
            proposal = journey.evaluation.proposal
            if proposal is None:
                return replace(
                    view, title='Nenhuma regra aplicável',
                    description=(
                        'A avaliação determinística não selecionou uma regra única; '
                        'nenhuma proposta foi criada.'
                    ),
                )
            rule_id = UUID(proposal['rule_version_id'])
            rule_name = self._repository.rule_name(
                tenant_id, company_id, rule_id,
            ) or 'Regra publicada sem nome disponível'
            return replace(
                view, title=f'Regra aplicada: {rule_name}',
                description=(
                    f'Versão {rule_id} selecionada deterministicamente por prioridade; '
                    'seu mapeamento definiu o débito e o crédito propostos.'
                ),
            )
        if event.action == 'accounting_proposal.created' and journey.lines:
            debit = sum(line.debit for line in journey.lines)
            credit = sum(line.credit for line in journey.lines)
            balance = 'equilibrada' if debit == credit else 'não equilibrada'
            return replace(
                view,
                description=(
                    f'Proposta {balance}, com débito total {debit} e crédito total '
                    f'{credit}, criada para revisão humana.'
                ),
            )
        return view

    def _active_lock_events(
        self, tenant_id: UUID, company_id: UUID, journey: Journey,
    ) -> list[tuple[datetime, str, DecisionLineEvent]]:
        result = []
        if journey.plan is None or journey.revision is None:
            return result
        groups = dict(journey.plan.account_groups)
        for record in self._repository.list_active_lock_records(tenant_id, company_id):
            blocked = False
            for line in journey.lines:
                account = next(item for item in journey.plan.accounts if item.id == line.account_version_id)
                try:
                    validate_effect((record.lock,), EffectContext(
                        tenant_id, company_id, account.account_id,
                        groups.get(account.account_id, ()), 'accounting',
                        journey.revision.accounting_date, EffectOperation.APPROVE,
                        EffectChannel.USER,
                    ))
                except AccountLockedError:
                    blocked = True
                    break
            if blocked:
                result.append((record.created_at, str(record.lock.id), DecisionLineEvent(
                    0, record.created_at, 'BLOCK', _GOVERNANCE,
                    'Governança do sistema', 'Decisão atualmente bloqueada',
                    'Um bloqueio vigente impede o efeito contábil neste escopo.',
                    'DOMAIN_DERIVED_EVENT', True,
                )))
        return result

    def _require(
        self, tenant_id: UUID, company_id: UUID, actor_id: UUID, permission: str,
    ) -> None:
        self._authorization.require(AuthorizationRequest(
            tenant_id, actor_id, PermissionCode(permission), company_id,
        ))
