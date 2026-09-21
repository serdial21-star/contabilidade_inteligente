from dataclasses import replace
from datetime import date, datetime, UTC
from decimal import Decimal
from uuid import uuid4

import pytest

from serdial21.modules.accounting.domain.classification import (
    ApprovedItemHistory, CompanyAccountingProfile, ItemEvidence, classify_item,
    normalize_description,
)
from serdial21.modules.chart_of_accounts.domain.entities import (
    AccountCodeMask, AccountVersion, assert_can_add_child,
    assert_hierarchy_acyclic, assert_unique_code,
)
from serdial21.modules.rules.domain.entities import AccountingRuleVersion
from serdial21.modules.accounting.domain.entities import (
    ItemAccountingAllocation, JournalEntryRevision, build_mixed_item_lines,
)


TODAY = date(2026, 9, 16)


def profile(segment: str, *, resale: bool = False, assets: bool = True) -> CompanyAccountingProfile:
    return CompanyAccountingProfile(uuid4(), uuid4(), segment, resells_goods=resale,
                                    controls_fixed_assets=assets)


def item(company_id, description: str, *, product='P1', gtin=None) -> ItemEvidence:
    return ItemEvidence(uuid4(), company_id, uuid4(), uuid4(), '12345678000199',
                        product, gtin, description, '84713012', '5102', '00', Decimal('100.00'))


def rule(company_id, intent: str, *, governance='COMPANY', priority=10,
         conditions=(('supplier_product_code', 'EQ', 'P1'),)) -> AccountingRuleVersion:
    return AccountingRuleVersion(uuid4(), uuid4(), company_id, uuid4(), 1, 'ITEM',
                                 conditions, priority, uuid4(), uuid4(), TODAY, None,
                                 'PUBLISHED', 'SUGGEST', True, True, governance, intent)


@pytest.mark.parametrize(('segment', 'resale', 'description', 'expected'), [
    ('SERVICES', False, 'Notebook Dell Latitude', 'PURCHASE_FIXED_ASSET'),
    ('TECHNOLOGY', True, 'Notebook Dell Latitude', 'PURCHASE_RESALE'),
    ('COMMERCE', True, 'Veículo novo', 'PURCHASE_RESALE'),
    ('SERVICES', False, 'Veículo administrativo', 'PURCHASE_FIXED_ASSET'),
    ('SERVICES', False, 'Papel A4', 'PURCHASE_USE_CONSUMPTION'),
])
def test_sc01_to_sc05_activity_is_evidence_not_absolute(
    segment: str, resale: bool, description: str, expected: str,
) -> None:
    company = uuid4()
    result = classify_item(item(company, description),
                           replace(profile(segment, resale=resale), company_id=company), (), at=TODAY)
    assert result.intent == expected
    assert result.confidence_level == 'MEDIUM'
    assert result.status == 'PRE_CLASSIFIED'


def test_sc06_reusable_approved_item_is_high_confidence_without_creating_rule() -> None:
    company = uuid4(); evidence = item(company, 'Produto recorrente', gtin='789000000001')
    history = ApprovedItemHistory('PURCHASE_FIXED_ASSET', True, 6,
                                  evidence.supplier_tax_id, evidence.supplier_product_code, evidence.gtin)
    result = classify_item(evidence, replace(profile('SERVICES'), company_id=company), (),
                           at=TODAY, history=history)
    assert (result.intent, result.confidence_level, result.status) == (
        'PURCHASE_FIXED_ASSET', 'HIGH', 'AUTO_CLASSIFIED')
    assert result.rule_version_id is None


def test_sc07_unknown_product_requires_review() -> None:
    company = uuid4()
    result = classify_item(item(company, 'Componente desconhecido'),
                           replace(profile('OTHER'), company_id=company), (), at=TODAY)
    assert (result.intent, result.status) == ('UNCLASSIFIED', 'REVIEW_REQUIRED')


def test_sc08_equal_company_rules_with_incompatible_intents_conflict() -> None:
    company = uuid4(); rules = (rule(company, 'PURCHASE_RESALE'), rule(company, 'PURCHASE_FIXED_ASSET'))
    result = classify_item(item(company, 'Notebook'), replace(profile('TECHNOLOGY'), company_id=company),
                           rules, at=TODAY)
    assert result.status == 'CONFLICTING_EVIDENCE'
    assert result.confidence_level == 'CONFLICT'


def test_sc09_and_sc10_company_rule_overrides_office_then_office_falls_back() -> None:
    company = uuid4(); base = item(company, 'Notebook')
    office = rule(company, 'PURCHASE_RESALE', governance='OFFICE', priority=100)
    company_rule = rule(company, 'PURCHASE_FIXED_ASSET', governance='COMPANY', priority=1)
    context = replace(profile('TECHNOLOGY', resale=True), company_id=company)
    assert classify_item(base, context, (office, company_rule), at=TODAY).intent == 'PURCHASE_FIXED_ASSET'
    assert classify_item(base, context, (office,), at=TODAY).intent == 'PURCHASE_RESALE'


def test_description_normalization_preserves_original_and_is_deterministic() -> None:
    assert normalize_description('  NOTEBOOK—Ágil... Dell  ') == 'notebook agil dell'


def account(*, tenant=None, company=None, account_id=None, parent=None,
            code='1.01', postable=True, synthetic=False):
    return AccountVersion(uuid4(), tenant or uuid4(), company or uuid4(), account_id or uuid4(), 1, code, 'Conta',
                          'ASSET', 'DEBIT', parent, synthetic, postable, 'PUBLISHED', TODAY, None)


def test_account_mask_hierarchy_uniqueness_and_used_account_protection() -> None:
    mask = AccountCodeMask(uuid4(), uuid4(), uuid4(), (1, 2, 2, 4), '.')
    mask.validate_code('1.02.03.0001')
    with pytest.raises(ValueError, match='máscara'):
        mask.validate_code('1.2.03.0001')
    tenant, company, parent_id = uuid4(), uuid4(), uuid4()
    parent = account(tenant=tenant, company=company, account_id=parent_id,
                     code='1.01', postable=False, synthetic=True)
    child = account(tenant=tenant, company=company, parent=parent_id, code='1.01.01')
    assert_hierarchy_acyclic(child, (parent, child))
    with pytest.raises(ValueError, match='duplicado'):
        assert_unique_code(replace(child, account_id=uuid4()), (child,))
    with pytest.raises(ValueError, match='usada'):
        assert_can_add_child(parent, {parent.account_id})


def test_mixed_nfe_builds_balanced_multi_intent_lines_with_item_traceability() -> None:
    tenant, company, ledger = uuid4(), uuid4(), uuid4()
    debit_accounts = tuple(AccountVersion(
        uuid4(), tenant, company, uuid4(), 1, f'5.0.{index}', f'Débito {index}',
        'EXPENSE', 'DEBIT', None, False, True, 'PUBLISHED', TODAY, None,
    ) for index in range(3))
    credit = AccountVersion(uuid4(), tenant, company, uuid4(), 1, '2.01', 'Fornecedor',
                            'LIABILITY', 'CREDIT', None, False, True, 'PUBLISHED', TODAY, None)
    revision = JournalEntryRevision(uuid4(), tenant, company, ledger, uuid4(), 1, TODAY,
                                    TODAY, TODAY, 'DRAFT', None)
    allocations = tuple(ItemAccountingAllocation(
        uuid4(), account.id, Decimal(value), intent,
    ) for account, value, intent in zip(
        debit_accounts, ('100.00', '25.50', '900.00'),
        ('PURCHASE_RESALE', 'PURCHASE_USE_CONSUMPTION', 'PURCHASE_FIXED_ASSET'), strict=True,
    ))
    lines, links = build_mixed_item_lines(revision, allocations, credit.id,
                                          (*debit_accounts, credit))
    assert len(lines) == 4 and len(links) == 3
    assert sum(line.debit for line in lines) == sum(line.credit for line in lines) == Decimal('1025.50')
    assert {link.source_item_id for link in links} == {item.source_item_id for item in allocations}
