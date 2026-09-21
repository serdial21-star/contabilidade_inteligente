'''Gates P1 do Accounting Automation Core.'''

from dataclasses import replace
from datetime import date
from decimal import Decimal
import re
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from test_nfe_to_dominio_vertical import FIXTURE, NOW, Environment, env
from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel, CompanyModel, PermissionModel, RoleBindingModel,
    RolePermissionModel, TenantMembershipModel, TenantModel,
)
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuthorizationRepository,
)
from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError, AuthorizationService,
)
from serdial21.modules.accounting.adapters.outbound.persistence.models import (
    ClassificationFeedbackModel, CompanyAccountingProfileModel,
    CompanyItemProfileModel, ItemClassificationModel,
)
from serdial21.modules.accounting.adapters.outbound.persistence.repositories import (
    SqlAlchemyAccountingClassificationRepository,
)
from serdial21.modules.accounting.application.services.classification import (
    ClassifyFiscalItem, ClassificationScopeError, ReviewClassificationCommand,
    ReviewItemClassification,
)
from serdial21.modules.accounting.domain.classification import ItemClassification, ItemEvidence
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.chart_of_accounts.domain.entities import AccountVersion
from serdial21.modules.fiscal_documents.adapters.outbound.persistence.models import FiscalDocumentItemModel
from serdial21.modules.mappings.domain.entities import MappingEntry, MappingVersion
from serdial21.modules.rules.domain.entities import AccountingRuleVersion, RuleSetRelease


def _grant_review(environment: Environment) -> None:
    session = environment.session
    membership = session.scalar(select(TenantMembershipModel).where(
        TenantMembershipModel.tenant_id == environment.tenant,
        TenantMembershipModel.user_id == environment.accountant,
    ))
    assert membership is not None
    role_id = session.scalar(select(RoleBindingModel.role_id).where(
        RoleBindingModel.tenant_id == environment.tenant,
        RoleBindingModel.membership_id == membership.id,
        RoleBindingModel.company_id == environment.company,
    ))
    assert role_id is not None
    permission = session.scalar(select(PermissionModel).where(
        PermissionModel.code == 'accounting.classification.review',
    ))
    if permission is None:
        permission = PermissionModel(
            id=uuid4(), code='accounting.classification.review',
            description='accounting.classification.review', version=1, is_active=True,
        )
        session.add(permission)
        session.flush()
    existing = session.scalar(select(RolePermissionModel.role_id).where(
        RolePermissionModel.tenant_id == environment.tenant,
        RolePermissionModel.role_id == role_id,
        RolePermissionModel.permission_id == permission.id,
    ))
    if existing is None:
        session.add(RolePermissionModel(
            tenant_id=environment.tenant, role_id=role_id, permission_id=permission.id,
        ))
    session.commit()


def _seed_classification(environment: Environment):
    environment.prepare()
    item_id = environment.session.scalar(select(FiscalDocumentItemModel.id).where(
        FiscalDocumentItemModel.tenant_id == environment.tenant,
        FiscalDocumentItemModel.company_id == environment.company,
    ))
    assert item_id is not None
    repository = SqlAlchemyAccountingClassificationRepository(environment.session)
    item = repository.get_item(environment.tenant, environment.company, item_id)
    assert item is not None
    record = repository.add_classification(
        item, ItemClassification(
            'PURCHASE_USE_CONSUMPTION', 'OFFICE_SUPPLY', 'MEDIUM',
            'PRE_CLASSIFIED', (),
        ), created_at=NOW,
    )
    environment.session.commit()
    return record


def _review_service(environment: Environment, audit: AuditService | None = None):
    return ReviewItemClassification(
        SqlAlchemyAccountingClassificationRepository(environment.session),
        AuthorizationService(SqlAlchemyAuthorizationRepository(environment.session)),
        audit or AuditService(SqlAlchemyAuditRepository(environment.session), clock=lambda: NOW),
        clock=lambda: NOW,
    )


def _review_command(environment: Environment, classification_id: UUID):
    return ReviewClassificationCommand(
        environment.tenant, environment.company, environment.accountant,
        classification_id, 'PURCHASE_FIXED_ASSET', 'CORRECTION',
        'SAME_ITEM_FUTURE', uuid4(),
    )


def test_classification_without_permission_is_denied(env: Environment) -> None:
    record = _seed_classification(env)
    with pytest.raises(AccessDeniedError):
        _review_service(env).execute(_review_command(env, record.id))
    env.session.rollback()
    assert env.session.scalar(select(func.count()).select_from(ClassificationFeedbackModel)) == 0


def test_classification_with_permission_without_company_access_is_denied(env: Environment) -> None:
    record = _seed_classification(env)
    _grant_review(env)
    access = env.session.get(CompanyAccessModel, env.accountant_access)
    assert access is not None
    access.status = 'revoked'
    env.session.commit()
    with pytest.raises(AccessDeniedError):
        _review_service(env).execute(_review_command(env, record.id))
    env.session.rollback()
    assert env.session.scalar(select(func.count()).select_from(ClassificationFeedbackModel)) == 0


def test_classification_with_permission_and_company_access_is_allowed(env: Environment) -> None:
    record = _seed_classification(env)
    _grant_review(env)
    reviewed = _review_service(env).execute(_review_command(env, record.id))
    env.session.commit()
    assert reviewed.classification.intent == 'PURCHASE_FIXED_ASSET'
    assert reviewed.version == 2
    assert env.session.scalar(select(func.count()).select_from(ClassificationFeedbackModel)) == 1
    assert env.session.scalar(select(func.count()).select_from(CompanyItemProfileModel)) == 1


def test_cross_tenant_and_company_classification_history_are_isolated(env: Environment) -> None:
    record = _seed_classification(env)
    _grant_review(env)
    wrong_company = replace(_review_command(env, record.id), company_id=uuid4())
    wrong_tenant = replace(_review_command(env, record.id), tenant_id=uuid4())
    for command in (wrong_company, wrong_tenant):
        with pytest.raises(AccessDeniedError):
            _review_service(env).execute(command)
        env.session.rollback()

    company_b = uuid4()
    with audit_scope(env.session, AuditContext(
        uuid4(), AuditOrigin.AUTOMATION, env.proposer, reason='P1 isolation fixture',
    )):
        env.session.add(CompanyModel(
            id=company_b, tenant_id=env.tenant, legal_name='Company B',
            tax_identifier='11111111111111', timezone='UTC', currency_code='BRL',
                status='active', valid_from=NOW,
            ))
        env.session.flush()
    for company_id, intent in (
        (env.company, 'PURCHASE_FIXED_ASSET'),
        (company_b, 'PURCHASE_RESALE'),
    ):
        env.session.add(CompanyItemProfileModel(
            id=uuid4(), tenant_id=env.tenant, company_id=company_id,
            counterparty_id=None, supplier_product_code='SAME-NOTEBOOK', gtin=None,
            ncm='84713012', normalized_description='notebook',
            identity_hash=str(uuid4()).replace('-', ''),
            preferred_accounting_intent=intent, occurrence_count=1,
            approved_count=1, last_used_at=NOW, status='ACTIVE',
        ))
    env.session.commit()
    repository = SqlAlchemyAccountingClassificationRepository(env.session)
    histories = []
    for company_id in (env.company, company_b):
        histories.append(repository.get_history(ItemEvidence(
            env.tenant, company_id, uuid4(), uuid4(), None, 'SAME-NOTEBOOK', None,
            'Notebook', '84713012', '1102', None, Decimal('100.00'),
        )))
    assert [history.intent for history in histories if history] == [
        'PURCHASE_FIXED_ASSET', 'PURCHASE_RESALE',
    ]


def test_classification_rejects_cross_scope_rule_before_persistence(env: Environment) -> None:
    record = _seed_classification(env)
    repository = SqlAlchemyAccountingClassificationRepository(env.session)
    item = repository.get_item(env.tenant, env.company, record.fiscal_item_id)
    assert item is not None
    env.session.add(CompanyAccountingProfileModel(
        tenant_id=env.tenant, company_id=env.company, business_segment='OTHER',
        auto_proposal_confidence_threshold='HIGH', version=1, updated_at=NOW,
    ))
    env.session.commit()
    foreign_rule = AccountingRuleVersion(
        uuid4(), uuid4(), env.company, uuid4(), 1, 'ITEM',
        (('supplier_product_code', 'EQ', item.supplier_product_code or ''),), 10,
        uuid4(), uuid4(), date(2026, 1, 1), None, 'PUBLISHED',
        'SUGGEST', True, True, 'COMPANY', 'PURCHASE_RESALE',
    )
    before = env.session.scalar(select(func.count()).select_from(ItemClassificationModel))
    with pytest.raises(ClassificationScopeError):
        ClassifyFiscalItem(repository, clock=lambda: NOW).execute(
            env.tenant, env.company, item, (foreign_rule,), at=NOW.date(),
        )
    env.session.rollback()
    assert env.session.scalar(select(func.count()).select_from(ItemClassificationModel)) == before


def test_classification_and_audit_commit_atomically(env: Environment) -> None:
    record = _seed_classification(env)
    _grant_review(env)
    reviewed = _review_service(env).execute(_review_command(env, record.id))
    env.session.commit()
    assert env.session.get(ItemClassificationModel, reviewed.id) is not None
    assert env.session.scalar(select(func.count()).select_from(AuditEventModel).where(
        AuditEventModel.subject_id == reviewed.id,
        AuditEventModel.action == 'item_classification.reviewed',
    )) == 1


def test_forced_audit_failure_rolls_back_classification_and_audit(env: Environment) -> None:
    record = _seed_classification(env)
    _grant_review(env)
    baseline_classifications = env.session.scalar(
        select(func.count()).select_from(ItemClassificationModel),
    )
    baseline_audits = env.session.scalar(select(func.count()).select_from(AuditEventModel))

    class FailingAuditRepository:
        def append(self, _: object) -> None:
            raise RuntimeError('forced audit failure')

    service = _review_service(
        env, AuditService(FailingAuditRepository(), clock=lambda: NOW),  # type: ignore[arg-type]
    )
    with pytest.raises(RuntimeError, match='forced audit failure'):
        service.execute(_review_command(env, record.id))
    env.session.rollback()
    assert env.session.scalar(select(func.count()).select_from(ItemClassificationModel)) == baseline_classifications
    assert env.session.scalar(select(func.count()).select_from(ClassificationFeedbackModel)) == 0
    assert env.session.scalar(select(func.count()).select_from(AuditEventModel)) == baseline_audits


def test_list_pending_filters_status_and_keeps_only_latest_version(env: Environment) -> None:
    record = _seed_classification(env)
    repository = SqlAlchemyAccountingClassificationRepository(env.session)
    item = repository.get_item(env.tenant, env.company, record.fiscal_item_id)
    assert item is not None

    rows, total = repository.list_pending(env.tenant, env.company, offset=0, limit=10)
    assert total == 0 and rows == ()

    pending = repository.add_classification(item, ItemClassification(
        'UNCLASSIFIED', None, 'LOW', 'REVIEW_REQUIRED', (),
    ), created_at=NOW)
    env.session.commit()
    assert pending.version == 2

    rows, total = repository.list_pending(env.tenant, env.company, offset=0, limit=10)
    assert total == 1
    assert [row.id for row in rows] == [pending.id]

    resolved = repository.add_classification(item, ItemClassification(
        'PURCHASE_USE_CONSUMPTION', 'OFFICE_SUPPLY', 'HIGH', 'AUTO_CLASSIFIED', (),
    ), created_at=NOW)
    env.session.commit()
    assert resolved.version == 3

    rows, total = repository.list_pending(env.tenant, env.company, offset=0, limit=10)
    assert total == 0 and rows == ()


def test_list_pending_is_scoped_by_tenant_and_company(env: Environment) -> None:
    record = _seed_classification(env)
    repository = SqlAlchemyAccountingClassificationRepository(env.session)
    item = repository.get_item(env.tenant, env.company, record.fiscal_item_id)
    assert item is not None
    repository.add_classification(item, ItemClassification(
        'UNCLASSIFIED', None, 'LOW', 'REVIEW_REQUIRED', (),
    ), created_at=NOW)
    env.session.commit()

    other_company_rows, other_company_total = repository.list_pending(
        env.tenant, uuid4(), offset=0, limit=10,
    )
    assert other_company_total == 0 and other_company_rows == ()
    other_tenant_rows, other_tenant_total = repository.list_pending(
        uuid4(), env.company, offset=0, limit=10,
    )
    assert other_tenant_total == 0 and other_tenant_rows == ()


def test_list_pending_paginates_across_two_items(env: Environment) -> None:
    record = _seed_classification(env)
    repository = SqlAlchemyAccountingClassificationRepository(env.session)
    item = repository.get_item(env.tenant, env.company, record.fiscal_item_id)
    assert item is not None
    first_pending = repository.add_classification(item, ItemClassification(
        'UNCLASSIFIED', None, 'LOW', 'REVIEW_REQUIRED', (),
    ), created_at=NOW)

    second_item_id = uuid4()
    env.session.add(FiscalDocumentItemModel(
        id=second_item_id, tenant_id=env.tenant, company_id=env.company,
        fiscal_document_id=record.fiscal_document_id, sequence=999,
        description='Segundo item sintético', gross_total=Decimal('10.00'),
    ))
    env.session.flush()
    second_item = repository.get_item(env.tenant, env.company, second_item_id)
    assert second_item is not None
    second_pending = repository.add_classification(second_item, ItemClassification(
        'UNCLASSIFIED', None, 'LOW', 'CONFLICTING_EVIDENCE', (),
    ), created_at=NOW)
    env.session.commit()

    first_page, total = repository.list_pending(env.tenant, env.company, offset=0, limit=1)
    assert total == 2
    assert len(first_page) == 1
    second_page, total_again = repository.list_pending(env.tenant, env.company, offset=1, limit=1)
    assert total_again == 2
    assert len(second_page) == 1
    assert {first_page[0].id, second_page[0].id} == {first_pending.id, second_pending.id}


def _mixed_xml() -> bytes:
    source = FIXTURE.read_text(encoding='utf-8')
    items = ''.join(
        f'''<det nItem="{sequence}"><prod><cProd>{code}</cProd><xProd>{description}</xProd>
        <NCM>84713012</NCM><CFOP>1102</CFOP><uCom>UN</uCom><qCom>1.000000</qCom>
        <vUnCom>{amount}</vUnCom><vProd>{amount}</vProd><indTot>1</indTot></prod></det>'''
        for sequence, code, description, amount in (
            (1, 'P1', 'Mercadoria para revenda', '100.00'),
            (2, 'P2', 'Papel para consumo', '25.50'),
            (3, 'P3', 'Notebook imobilizado', '900.00'),
        )
    )
    source = re.sub(r'<det nItem=.*?</det>', items, source, count=1, flags=re.DOTALL)
    source = re.sub(
        r'<total>.*?</total>',
        '<total><ICMSTot><vProd>1025.50</vProd><vFrete>0.00</vFrete>'
        '<vSeg>0.00</vSeg><vDesc>0.00</vDesc><vOutro>0.00</vOutro>'
        '<vTotTrib>0.00</vTotTrib><vNF>1025.50</vNF></ICMSTot></total>',
        source, count=1, flags=re.DOTALL,
    )
    return source.encode()


def _configure_mixed(environment: Environment) -> None:
    tenant, company = environment.tenant, environment.company
    debit_accounts = tuple(AccountVersion(
        uuid4(), tenant, company, uuid4(), 1, f'5.{index}', name,
        'EXPENSE', 'DEBIT', None, False, True, 'PUBLISHED', date(2026, 1, 1), None,
    ) for index, name in enumerate(('Revenda', 'Consumo', 'Imobilizado'), start=1))
    credit = AccountVersion(
        uuid4(), tenant, company, uuid4(), 1, '2.1', 'Fornecedor',
        'LIABILITY', 'CREDIT', None, False, True, 'PUBLISHED', date(2026, 1, 1), None,
    )
    document_rule = AccountingRuleVersion(
        uuid4(), tenant, company, uuid4(), 1, 'NFE55', (('model', 'EQ', '55'),),
        1, debit_accounts[0].id, credit.id, date(2026, 1, 1), None,
        'PUBLISHED', 'SUGGEST', True, True,
    )
    intents = (
        'PURCHASE_RESALE', 'PURCHASE_USE_CONSUMPTION', 'PURCHASE_FIXED_ASSET',
    )
    item_rules = tuple(AccountingRuleVersion(
        uuid4(), tenant, company, uuid4(), 1, 'ITEM',
        (('supplier_product_code', 'EQ', f'P{index}'),), 10,
        account.id, credit.id, date(2026, 1, 1), None, 'PUBLISHED',
        'SUGGEST', True, True, 'COMPANY', intent,
    ) for index, (intent, account) in enumerate(zip(intents, debit_accounts, strict=True), start=1))
    mapping_version = MappingVersion(
        uuid4(), tenant, company, uuid4(), 1, 'PUBLISHED', date(2026, 1, 1), None,
    )
    mappings = tuple(MappingEntry(
        uuid4(), tenant, company, mapping_version.id, 10,
        None, None, None, 'FiscalDocumentItem', account.id, None,
        date(2026, 1, 1), None, intent, None,
    ) for intent, account in zip(intents, debit_accounts, strict=True))
    plan = environment.catalog.plan
    assert plan is not None
    accounts = (*debit_accounts, credit)
    environment.catalog.plan = replace(
        plan, rules=(document_rule, *item_rules), accounts=accounts,
        release=RuleSetRelease(
            uuid4(), tenant, company, 'P1 MIXED',
            tuple(rule.id for rule in (document_rule, *item_rules)), 'PUBLISHED',
        ),
        account_groups=tuple((account.account_id, ()) for account in accounts),
        mapping_version=mapping_version, mapping_entries=mappings,
    )
    environment.session.add(CompanyAccountingProfileModel(
        tenant_id=tenant, company_id=company, business_segment='OTHER',
        keeps_inventory=None, manufactures_goods=None, resells_goods=None,
        provides_services=None, uses_cost_centers=None, uses_projects=None,
        controls_fixed_assets=None, capitalization_threshold=None,
        minimum_useful_life_months=None, capitalizes_freight_to_inventory=None,
        auto_proposal_confidence_threshold='HIGH', version=1, updated_at=NOW,
    ))
    environment.session.commit()


def test_mixed_nfe_three_item_end_to_end(env: Environment) -> None:
    _configure_mixed(env)
    journey = env.runtime().prepare(
        replace(env.command(), idempotency_key='mixed-nfe-p1'),
        content=_mixed_xml(), filename='mixed-p1.xml',
    )
    env.session.commit()
    items = tuple(env.session.scalars(select(FiscalDocumentItemModel).where(
        FiscalDocumentItemModel.tenant_id == env.tenant,
        FiscalDocumentItemModel.company_id == env.company,
        FiscalDocumentItemModel.fiscal_document_id == journey.imported.fiscal_document_id,
    ).order_by(FiscalDocumentItemModel.sequence)))
    classifications = tuple(env.session.scalars(select(ItemClassificationModel).where(
        ItemClassificationModel.tenant_id == env.tenant,
        ItemClassificationModel.company_id == env.company,
    ).order_by(ItemClassificationModel.fiscal_document_item_id)))
    assert journey.status == 'PENDING_APPROVAL'
    assert len(items) == len(classifications) == len(journey.line_sources) == 3
    assert {item.selected_intent for item in classifications} == {
        'PURCHASE_RESALE', 'PURCHASE_USE_CONSUMPTION', 'PURCHASE_FIXED_ASSET',
    }
    assert {link.source_item_id for link in journey.line_sources} == {item.id for item in items}
    assert len(journey.lines) == 4
    assert sum(line.debit for line in journey.lines) == Decimal('1025.50')
    assert sum(line.credit for line in journey.lines) == Decimal('1025.50')


def test_mixed_nfe_rejects_cross_company_mapping(env: Environment) -> None:
    _configure_mixed(env)
    plan = env.catalog.plan
    assert plan is not None
    assert plan.mapping_version is not None
    env.catalog.plan = replace(
        plan,
        mapping_version=replace(plan.mapping_version, company_id=uuid4()),
    )

    journey = env.runtime().prepare(
        replace(env.command(), idempotency_key='mixed-nfe-cross-company-mapping'),
        content=_mixed_xml(), filename='mixed-cross-company.xml',
    )
    env.session.commit()

    assert journey.status == 'ACCOUNT_MAPPING_REQUIRED'
    assert journey.lines == ()
    assert journey.line_sources == ()
