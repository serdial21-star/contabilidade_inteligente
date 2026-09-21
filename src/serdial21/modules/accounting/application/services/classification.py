'''Classificação persistente e revisão humana autorizada.'''

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError, AuthorizationRequest, AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.accounting.application.ports.repository import (
    AccountingClassificationRepository, ClassificationRecord,
)
from serdial21.modules.accounting.domain.classification import (
    ACCOUNTING_INTENTS, ClassificationEvidence, ItemClassification, ItemEvidence,
    classify_item,
)
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.rules.domain.entities import AccountingRuleVersion


class ClassificationUnavailableError(LookupError):
    def __init__(self) -> None:
        super().__init__('resource unavailable')


class ClassificationScopeError(PermissionError):
    def __init__(self) -> None:
        super().__init__('access denied')


class ClassifyFiscalItem:
    '''Executa somente classificação determinística dentro de um escopo confiável.'''

    def __init__(self, repository: AccountingClassificationRepository,
                 *, clock: Callable[[], datetime] | None = None) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(self, tenant_id: UUID, company_id: UUID, item: ItemEvidence,
                rules: tuple[AccountingRuleVersion, ...], *, at: date) -> ClassificationRecord:
        if (item.tenant_id, item.company_id) != (tenant_id, company_id):
            raise ClassificationScopeError()
        profile = self._repository.get_profile(tenant_id, company_id)
        if profile is None:
            raise ClassificationUnavailableError()
        if (profile.tenant_id, profile.company_id) != (tenant_id, company_id):
            raise ClassificationScopeError()
        if any((rule.tenant_id, rule.company_id) != (tenant_id, company_id) for rule in rules):
            raise ClassificationScopeError()
        history = self._repository.get_history(item)
        result = classify_item(item, profile, rules, at=at, history=history)
        return self._repository.add_classification(item, result, created_at=self._now())

    def is_configured(self, tenant_id: UUID, company_id: UUID) -> bool:
        return self._repository.get_profile(tenant_id, company_id) is not None

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError('clock requires timezone')
        return now.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ReviewClassificationCommand:
    tenant_id: UUID
    company_id: UUID
    actor_id: UUID
    classification_id: UUID
    final_intent: str
    decision_type: str
    apply_scope: str
    correlation_id: UUID


class ReviewItemClassification:
    '''Decisão humana autorizada; persistência e auditoria usam a mesma UoW.'''

    def __init__(self, repository: AccountingClassificationRepository,
                 authorization: AuthorizationService, audit: AuditService,
                 *, clock: Callable[[], datetime] | None = None) -> None:
        self._repository = repository
        self._authorization = authorization
        self._audit = audit
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(self, command: ReviewClassificationCommand) -> ClassificationRecord:
        now = self._now()
        self._authorization.require(AuthorizationRequest(
            command.tenant_id, command.actor_id,
            PermissionCode('accounting.classification.review'), command.company_id,
        ), at=now)
        if command.final_intent not in ACCOUNTING_INTENTS or command.final_intent == 'UNCLASSIFIED':
            raise ValueError('intenção final inválida')
        if command.apply_scope not in {
            'THIS_OCCURRENCE_ONLY', 'SAME_ITEM_FUTURE', 'CREATE_RULE_REQUEST',
        }:
            raise ValueError('escopo de decisão inválido')
        current = self._repository.get_classification(
            command.tenant_id, command.company_id, command.classification_id,
        )
        if current is None:
            raise ClassificationUnavailableError()
        item = self._repository.get_item(
            command.tenant_id, command.company_id, current.fiscal_item_id,
        )
        if item is None or item.fiscal_document_id != current.fiscal_document_id:
            raise ClassificationUnavailableError()
        reviewed = ItemClassification(
            command.final_intent, current.classification.category, 'HIGH', 'REVIEWED',
            (ClassificationEvidence(
                'HUMAN_DECISION', command.final_intent, 100,
                'Classificação confirmada por decisão profissional', command.actor_id,
            ),),
        )
        result = self._repository.add_classification(item, reviewed, created_at=now)
        if self._repository.feedback_exists(
            result, final_intent=command.final_intent,
            apply_scope=command.apply_scope, actor_id=command.actor_id,
        ):
            return result
        self._repository.add_feedback(
            result, original_intent=current.classification.intent,
            final_intent=command.final_intent, decision_type=command.decision_type,
            apply_scope=command.apply_scope, actor_id=command.actor_id, decided_at=now,
        )
        if command.apply_scope == 'SAME_ITEM_FUTURE':
            self._repository.save_reusable_history(item, intent=command.final_intent, used_at=now)
        self._audit.record(AuditRecord(
            tenant_id=command.tenant_id, company_id=command.company_id,
            actor_id=command.actor_id, origin=AuditOrigin.HUMAN,
            module='accounting', action='item_classification.reviewed',
            subject_type='ItemClassification', subject_id=result.id,
            subject_version=result.version,
            before={'intent': current.classification.intent, 'status': current.classification.status},
            after={'intent': command.final_intent, 'status': reviewed.status,
                   'apply_scope': command.apply_scope},
            reason=command.decision_type, correlation_id=command.correlation_id,
        ))
        self._repository.flush()
        return result

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError('clock requires timezone')
        return now.astimezone(UTC)
