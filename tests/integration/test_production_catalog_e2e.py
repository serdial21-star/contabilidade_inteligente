'''Catálogo real -> publicação -> documento -> nova versão -> histórico.'''

from dataclasses import replace
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from test_nfe_to_dominio_vertical import FIXTURE, NOW, Environment, env
from serdial21.bootstrap.nfe_to_dominio import create_nfe_to_dominio_runtime
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    PermissionModel, RoleBindingModel, RolePermissionModel, TenantMembershipModel,
)
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuthorizationRepository,
)
from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError, AuthorizationService,
)
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.catalog.adapters.outbound.persistence.models import (
    ProductionCatalogVersionModel,
)
from serdial21.modules.catalog.adapters.outbound.persistence.repositories import (
    SqlAlchemyProductionCatalogRepository,
)
from serdial21.modules.catalog.application.services.governance import CatalogGovernanceService
from serdial21.modules.catalog.domain.entities import (
    AccountSpec, CatalogSpec, MappingEntrySpec, RuleSpec, WorkflowSpec,
)
from serdial21.modules.workflow.application.journey import JourneyCommand


def _spec(version: int, *, valid_from: date) -> CatalogSpec:
    return CatalogSpec(
        name='Catálogo operacional NF-e',
        ledger_name='Livro operacional BRL',
        currency_code='BRL',
        chart_name='Plano operacional',
        accounts=(
            AccountSpec('asset', '1.1', 'Conta débito', 'ASSET', 'DEBIT', None, False, True),
            AccountSpec('revenue', '3.1', 'Conta crédito', 'REVENUE', 'CREDIT', None, False, True),
        ),
        rules=(RuleSpec(
            'nfe55', f'Regra NF-e versão {version}', 'NFE55',
            (('model', 'EQ', '55'),), 10, 'asset', 'revenue', 'SUGGEST', True,
        ),),
        mapping_name='DE/PARA operacional',
        mapping_namespace='NFE55',
        mappings=(MappingEntrySpec(
            'nfe55-asset', 10, 'asset', canonical_entity='FiscalDocument',
        ),),
        workflow=WorkflowSpec('Revisão contábil', 'CONTADOR', 'CONTADOR'),
        amount_field='invoice_total',
        decimal_places=2,
        valid_from=valid_from,
        valid_to=None,
    )


def _governance(environment: Environment) -> CatalogGovernanceService:
    return CatalogGovernanceService(
        SqlAlchemyProductionCatalogRepository(environment.session),
        AuthorizationService(SqlAlchemyAuthorizationRepository(environment.session)),
        AuditService(SqlAlchemyAuditRepository(environment.session), clock=lambda: NOW),
        clock=lambda: NOW,
    )


def _grant_catalog_permissions(environment: Environment) -> None:
    session = environment.session
    proposer_membership = session.scalar(select(TenantMembershipModel).where(
        TenantMembershipModel.tenant_id == environment.tenant,
        TenantMembershipModel.user_id == environment.proposer,
    ))
    accountant_membership = session.scalar(select(TenantMembershipModel).where(
        TenantMembershipModel.tenant_id == environment.tenant,
        TenantMembershipModel.user_id == environment.accountant,
    ))
    assert proposer_membership and accountant_membership
    proposer_role = session.scalar(select(RoleBindingModel.role_id).where(
        RoleBindingModel.membership_id == proposer_membership.id,
    ))
    accountant_role = session.scalar(select(RoleBindingModel.role_id).where(
        RoleBindingModel.membership_id == accountant_membership.id,
    ))
    assert proposer_role and accountant_role
    for code in ('catalog.manage', 'catalog.review'):
        permission = PermissionModel(
            id=uuid4(), code=code, description=code, version=1, is_active=True,
        )
        session.add(permission)
        session.flush()
        session.add(RolePermissionModel(
            tenant_id=environment.tenant,
            role_id=proposer_role,
            permission_id=permission.id,
        ))
        if code == 'catalog.review':
            session.add(RolePermissionModel(
                tenant_id=environment.tenant,
                role_id=accountant_role,
                permission_id=permission.id,
            ))
    session.commit()


def _command(environment: Environment, key: str, accounting_date: date) -> JourneyCommand:
    return JourneyCommand(
        environment.tenant, environment.company, environment.proposer, key,
        accounting_date, date(2026, 9, 1), date(2026, 9, 30),
        NOW + timedelta(days=1),
    )


def test_governed_catalog_versions_drive_real_document_journey(env: Environment) -> None:
    _grant_catalog_permissions(env)
    governance = _governance(env)
    correlation_v1 = uuid4()
    draft_v1 = governance.create_draft(
        env.tenant, env.company, env.proposer, _spec(1, valid_from=date(2026, 1, 1)),
        correlation_id=correlation_v1, reason='configuração inicial aprovada',
    )
    assert draft_v1.status == 'DRAFT'
    env.session.commit()
    review_v1 = governance.submit_review(
        env.tenant, env.company, env.proposer, draft_v1.id,
        correlation_id=correlation_v1, reason='submeter revisão independente',
    )
    assert review_v1.status == 'REVIEW'
    env.session.commit()
    with pytest.raises(PermissionError, match='segregação'):
        governance.publish(
            env.tenant, env.company, env.proposer, review_v1.id,
            correlation_id=correlation_v1, reason='autor não pode publicar',
        )
    env.session.rollback()
    published_v1 = governance.publish(
        env.tenant, env.company, env.accountant, review_v1.id,
        correlation_id=correlation_v1, reason='revisão contábil concluída',
    )
    env.session.commit()
    assert published_v1.status == 'PUBLISHED'

    runtime = create_nfe_to_dominio_runtime(
        env.session, env.settings, clock=lambda: NOW,
    )
    journey_v1 = runtime.prepare(
        _command(env, 'persistent-catalog-v1', date(2026, 9, 4)),
        content=FIXTURE.read_bytes(), filename='catalog-v1.xml',
    )
    env.session.commit()
    assert journey_v1.status == 'PENDING_APPROVAL'
    assert journey_v1.plan is not None
    assert journey_v1.plan.rules[0].version_no == 1
    assert journey_v1.item is not None and journey_v1.item.role == 'CONTADOR'
    assert journey_v1.step is not None and journey_v1.step.role == 'CONTADOR'

    immutable = env.session.get(ProductionCatalogVersionModel, published_v1.id)
    assert immutable is not None
    immutable.status = 'DRAFT'
    with pytest.raises(ValueError, match='imutável'):
        env.session.flush()
    env.session.rollback()

    correlation_v2 = uuid4()
    draft_v2 = governance.create_next_draft(
        env.tenant, env.company, env.proposer, published_v1.id,
        _spec(2, valid_from=date(2026, 9, 5)),
        correlation_id=correlation_v2, reason='alteração versionada da regra',
    )
    assert draft_v2.version_no == 2
    assert draft_v2.supersedes_version_id == published_v1.id
    governance.submit_review(
        env.tenant, env.company, env.proposer, draft_v2.id,
        correlation_id=correlation_v2, reason='nova versão para revisão',
    )
    published_v2 = governance.publish(
        env.tenant, env.company, env.accountant, draft_v2.id,
        correlation_id=correlation_v2, reason='nova versão revisada',
    )
    env.session.commit()

    journey_v2 = runtime.prepare(
        _command(env, 'persistent-catalog-v2', date(2026, 9, 6)),
        content=FIXTURE.read_bytes(), filename='catalog-v2.xml',
    )
    env.session.commit()
    assert journey_v2.status == 'PENDING_APPROVAL'
    assert journey_v2.plan is not None
    assert journey_v2.plan.rules[0].version_no == 2
    assert journey_v2.plan.release.id != journey_v1.plan.release.id
    assert journey_v2.plan.rules[0].id != journey_v1.plan.rules[0].id

    history = list(env.session.scalars(select(
        ProductionCatalogVersionModel,
    ).order_by(ProductionCatalogVersionModel.version_no)))
    assert [(item.version_no, item.status) for item in history] == [
        (1, 'PUBLISHED'), (2, 'PUBLISHED'),
    ]
    assert history[0].content['rules'][0]['name'] == 'Regra NF-e versão 1'
    assert history[1].content['rules'][0]['name'] == 'Regra NF-e versão 2'
    assert history[0].content['accounts'][0]['version_no'] == 1
    assert history[1].content['accounts'][0]['version_no'] == 2
    assert history[0].content['accounts'][0]['account_id'] == (
        history[1].content['accounts'][0]['account_id']
    )
    assert history[0].content['rules'][0]['rule_id'] == history[1].content['rules'][0]['rule_id']
    assert history[0].content['mapping']['version_no'] == 1
    assert history[1].content['mapping']['version_no'] == 2
    assert history[1].content['workflow']['responsible_role'] == 'CONTADOR'
    assert history[1].content['mapping']['entries'][0]['target_account_version_id'] == (
        history[1].content['accounts'][0]['id']
    )
    assert history[0].created_by == env.proposer
    assert history[0].reviewed_by == history[0].published_by == env.accountant
    assert history[0].content_hash != history[1].content_hash
    actions = list(env.session.scalars(select(AuditEventModel.action).where(
        AuditEventModel.tenant_id == env.tenant,
        AuditEventModel.module == 'catalog',
    )))
    assert actions.count('catalog.published') == 2
    assert set(actions) >= {
        'catalog.draft.created', 'catalog.review.requested',
        'catalog.version.created', 'catalog.published',
    }
    audit = AuditService(SqlAlchemyAuditRepository(env.session), clock=lambda: NOW)
    events = (
        audit.list_by_correlation(env.tenant, correlation_v1)
        + audit.list_by_correlation(env.tenant, correlation_v2)
    )
    assert all(audit.verify_integrity(event) for event in events)


def test_catalog_governance_denies_untrusted_tenant_scope(env: Environment) -> None:
    _grant_catalog_permissions(env)
    with pytest.raises(AccessDeniedError):
        _governance(env).create_draft(
            uuid4(), env.company, env.proposer,
            _spec(1, valid_from=date(2026, 1, 1)),
            correlation_id=uuid4(), reason='cross-tenant must fail',
        )


def test_catalog_cannot_publish_rule_without_test_evidence(env: Environment) -> None:
    _grant_catalog_permissions(env)
    governance = _governance(env)
    spec = _spec(1, valid_from=date(2026, 1, 1))
    spec = replace(spec, rules=(replace(spec.rules[0], tests_passed=False),))
    correlation = uuid4()
    draft = governance.create_draft(
        env.tenant, env.company, env.proposer, spec,
        correlation_id=correlation, reason='regra ainda não testada',
    )
    env.session.commit()
    governance.submit_review(
        env.tenant, env.company, env.proposer, draft.id,
        correlation_id=correlation, reason='revisão deve bloquear publicação',
    )
    env.session.commit()
    with pytest.raises(ValueError, match='sem testes'):
        governance.publish(
            env.tenant, env.company, env.accountant, draft.id,
            correlation_id=correlation, reason='publicação proibida',
        )
    env.session.rollback()
