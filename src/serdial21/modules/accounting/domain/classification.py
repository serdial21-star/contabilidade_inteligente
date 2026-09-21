'''Classificação contábil determinística por item; intenção nunca é uma conta.'''

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import re
import unicodedata
from uuid import UUID

from serdial21.modules.rules.domain.entities import AccountingRuleVersion


ACCOUNTING_INTENTS = frozenset({
    'PURCHASE_RESALE', 'PURCHASE_RAW_MATERIAL', 'PURCHASE_PACKAGING',
    'PURCHASE_USE_CONSUMPTION', 'PURCHASE_FIXED_ASSET', 'PURCHASE_SERVICE',
    'PURCHASE_MAINTENANCE', 'PURCHASE_FREIGHT', 'PURCHASE_ADMIN_EXPENSE',
    'PURCHASE_PROJECT_COST', 'PURCHASE_PREPAID_EXPENSE', 'PURCHASE_OTHER',
    'UNCLASSIFIED',
})
BUSINESS_SEGMENTS = frozenset({
    'COMMERCE', 'SERVICES', 'INDUSTRY', 'CONSTRUCTION', 'TRANSPORT',
    'AGRIBUSINESS', 'HEALTH', 'EDUCATION', 'TECHNOLOGY', 'HOLDING', 'OTHER',
})
RULE_SCOPE_RANK = {'SYSTEM_TEMPLATE': 1, 'OFFICE': 2, 'COMPANY': 3}


@dataclass(frozen=True, slots=True)
class CompanyBusinessActivity:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    cnae_code: str
    description: str | None
    is_primary: bool
    is_active: bool
    effective_from: date
    effective_to: date | None = None

    def validate(self) -> None:
        if not re.fullmatch(r'\d{7}', normalize_cnae(self.cnae_code)):
            raise ValueError('CNAE inválido')
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError('vigência de CNAE inválida')


@dataclass(frozen=True, slots=True)
class CompanyAccountingProfile:
    tenant_id: UUID
    company_id: UUID
    business_segment: str
    keeps_inventory: bool | None = None
    manufactures_goods: bool | None = None
    resells_goods: bool | None = None
    provides_services: bool | None = None
    uses_cost_centers: bool | None = None
    uses_projects: bool | None = None
    controls_fixed_assets: bool | None = None
    capitalization_threshold: Decimal | None = None
    minimum_useful_life_months: int | None = None
    capitalizes_freight_to_inventory: bool | None = None
    auto_proposal_confidence_threshold: str = 'HIGH'

    def validate(self) -> None:
        if self.business_segment not in BUSINESS_SEGMENTS:
            raise ValueError('segmento empresarial inválido')
        if self.capitalization_threshold is not None and self.capitalization_threshold < 0:
            raise ValueError('limite de capitalização inválido')
        if self.minimum_useful_life_months is not None and self.minimum_useful_life_months < 1:
            raise ValueError('vida útil mínima inválida')
        if self.auto_proposal_confidence_threshold not in {'HIGH', 'NEVER'}:
            raise ValueError('política de automação inválida')


@dataclass(frozen=True, slots=True)
class ItemEvidence:
    tenant_id: UUID
    company_id: UUID
    fiscal_document_id: UUID
    fiscal_item_id: UUID
    supplier_tax_id: str | None
    supplier_product_code: str | None
    gtin: str | None
    description: str
    ncm: str | None
    document_cfop: str | None
    cst: str | None
    gross_total: Decimal
    direction: str = 'ENTRADA'

    def rule_input(self, profile: CompanyAccountingProfile) -> dict[str, str]:
        return {
            'company_id': str(self.company_id), 'business_segment': profile.business_segment,
            'supplier_tax_id': self.supplier_tax_id or '',
            'supplier_product_code': self.supplier_product_code or '', 'gtin': self.gtin or '',
            'description': normalize_description(self.description), 'ncm': digits(self.ncm),
            'cfop': digits(self.document_cfop), 'cst': digits(self.cst),
            'direction': self.direction, 'gross_total': str(self.gross_total),
        }


@dataclass(frozen=True, slots=True)
class ApprovedItemHistory:
    intent: str
    reusable: bool
    approved_count: int
    supplier_tax_id: str | None
    supplier_product_code: str | None
    gtin: str | None


@dataclass(frozen=True, slots=True)
class ClassificationEvidence:
    kind: str
    intent: str
    weight: int
    explanation: str
    reference_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ItemClassification:
    intent: str
    category: str | None
    confidence_level: str
    status: str
    evidence: tuple[ClassificationEvidence, ...]
    rule_version_id: UUID | None = None
    alternatives: tuple[str, ...] = ()


def classify_item(
    item: ItemEvidence, profile: CompanyAccountingProfile,
    rules: tuple[AccountingRuleVersion, ...], *, at: date,
    history: ApprovedItemHistory | None = None,
) -> ItemClassification:
    profile.validate()
    source = item.rule_input(profile)
    matched = [rule for rule in rules if _classification_rule_matches(rule, source, at)]
    if matched:
        scope = max(RULE_SCOPE_RANK.get(rule.governance_scope, 0) for rule in matched)
        scoped = [rule for rule in matched if RULE_SCOPE_RANK.get(rule.governance_scope, 0) == scope]
        priority = max(rule.priority for rule in scoped)
        winners = [rule for rule in scoped if rule.priority == priority]
        intents = {rule.intent for rule in winners}
        if len(intents) != 1:
            return _conflict(tuple(ClassificationEvidence(
                'RULE_MATCH', rule.intent or 'UNCLASSIFIED', 100,
                f'Regras incompatíveis no escopo {rule.governance_scope}', rule.id,
            ) for rule in winners))
        winner = winners[0]
        confidence = winner.confidence_override or 'HIGH'
        return _result(winner.intent or 'UNCLASSIFIED', winner.classification_category,
                       confidence, (ClassificationEvidence(
                           'RULE_MATCH', winner.intent or 'UNCLASSIFIED', 100,
                           f'Regra {winner.governance_scope} explícita e vigente', winner.id,
                       ),), rule_version_id=winner.id,
                       auto_threshold=profile.auto_proposal_confidence_threshold)
    if history and history.reusable and _same_product(item, history):
        return _result(history.intent, None, 'HIGH', (ClassificationEvidence(
            'PREVIOUS_APPROVAL', history.intent, 90,
            f'Classificação reutilizável aprovada {history.approved_count} vez(es)',
        ),), auto_threshold=profile.auto_proposal_confidence_threshold)
    category = _category(normalize_description(item.description))
    candidates: list[ClassificationEvidence] = []
    if category in {'IT_EQUIPMENT', 'VEHICLE'}:
        if profile.resells_goods and profile.business_segment in {'COMMERCE', 'TECHNOLOGY'}:
            candidates.append(ClassificationEvidence('BUSINESS_ACTIVITY_FIT', 'PURCHASE_RESALE', 55,
                                                      'Produto compatível com atividade declarada de revenda'))
        elif profile.controls_fixed_assets:
            candidates.append(ClassificationEvidence('BUSINESS_ACTIVITY_FIT', 'PURCHASE_FIXED_ASSET', 45,
                                                      'Bem durável compatível com controle de imobilizado'))
    elif category == 'OFFICE_SUPPLY':
        candidates.append(ClassificationEvidence('DESCRIPTION_MATCH', 'PURCHASE_USE_CONSUMPTION', 45,
                                                  'Categoria determinística de material de uso/consumo'))
    supported = {e.intent for e in candidates}
    if len(supported) > 1:
        return _conflict(tuple(candidates))
    if supported:
        intent = next(iter(supported))
        if item.ncm:
            candidates.append(ClassificationEvidence('NCM_MATCH', intent, 10, 'NCM como evidência de apoio'))
        if item.document_cfop:
            candidates.append(ClassificationEvidence('CFOP_MATCH', intent, 5, 'CFOP somente como evidência de apoio'))
        return _result(intent, category, 'MEDIUM', tuple(candidates),
                       auto_threshold=profile.auto_proposal_confidence_threshold)
    return _result('UNCLASSIFIED', category, 'LOW', tuple(candidates),
                   auto_threshold=profile.auto_proposal_confidence_threshold)


def normalize_description(value: str) -> str:
    folded = unicodedata.normalize('NFKD', value.casefold())
    ascii_text = ''.join(char for char in folded if not unicodedata.combining(char))
    return ' '.join(re.findall(r'[a-z0-9]+', ascii_text))


def normalize_cnae(value: str) -> str:
    return digits(value)


def digits(value: str | None) -> str:
    return ''.join(char for char in (value or '') if char.isdigit())


def _classification_rule_matches(rule: AccountingRuleVersion, source: dict[str, str], at: date) -> bool:
    if not rule.intent or rule.intent not in ACCOUNTING_INTENTS:
        return False
    if rule.status != 'PUBLISHED' or at < rule.valid_from or (rule.valid_to and at > rule.valid_to):
        return False
    for field, operator, expected in rule.conditions:
        actual = source.get(field)
        if operator == 'EQ' and actual != expected: return False
        if operator == 'CONTAINS' and (actual is None or expected.casefold() not in actual.casefold()): return False
        if operator == 'PREFIX' and (actual is None or not actual.startswith(expected)): return False
        if operator == 'GTE' and (actual is None or Decimal(actual) < Decimal(expected)): return False
        if operator == 'LTE' and (actual is None or Decimal(actual) > Decimal(expected)): return False
        if operator not in {'EQ', 'CONTAINS', 'PREFIX', 'GTE', 'LTE'}:
            raise ValueError('operador DSL não permitido')
    return True


def _same_product(item: ItemEvidence, history: ApprovedItemHistory) -> bool:
    if history.supplier_tax_id and history.supplier_tax_id != item.supplier_tax_id: return False
    return bool((history.gtin and history.gtin == item.gtin) or
                (history.supplier_product_code and history.supplier_product_code == item.supplier_product_code))


def _category(normalized: str) -> str | None:
    tokens = set(normalized.split())
    if tokens & {'notebook', 'laptop', 'computador', 'desktop'}: return 'IT_EQUIPMENT'
    if tokens & {'veiculo', 'automovel', 'carro', 'caminhao'}: return 'VEHICLE'
    if tokens & {'papel', 'caneta', 'grampeador', 'toner'}: return 'OFFICE_SUPPLY'
    return None


def _result(intent: str, category: str | None, confidence: str,
            evidence: tuple[ClassificationEvidence, ...], *,
            rule_version_id: UUID | None = None, auto_threshold: str) -> ItemClassification:
    status = {'HIGH': 'AUTO_CLASSIFIED' if auto_threshold == 'HIGH' else 'PRE_CLASSIFIED',
              'MEDIUM': 'PRE_CLASSIFIED', 'LOW': 'REVIEW_REQUIRED'}[confidence]
    return ItemClassification(intent, category, confidence, status, evidence, rule_version_id)


def _conflict(evidence: tuple[ClassificationEvidence, ...]) -> ItemClassification:
    return ItemClassification('UNCLASSIFIED', None, 'CONFLICT', 'CONFLICTING_EVIDENCE',
                              evidence, alternatives=tuple(sorted({item.intent for item in evidence})))
