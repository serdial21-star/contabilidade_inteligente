"""Integração real até o gate Domínio; dados e atos humanos são apenas fixtures."""
from collections.abc import Iterator
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from test_nfe55_bootstrap import seed_authorized_actor
from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, create_database_engine, create_session_factory
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.nfe_to_dominio import create_nfe_to_dominio_runtime
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel, PermissionModel, RoleBindingModel, RoleModel, RolePermissionModel,
    TenantMembershipModel, UserModel,
)
from serdial21.modules.access_control.application.services.authorization import AccessDeniedError
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.chart_of_accounts.domain.entities import AccountVersion, Ledger
from serdial21.modules.integrations.adapters.outbound.dominio import DominioConnector
from serdial21.modules.integrations.application.ports.connector import ConnectorConfiguration
from serdial21.modules.intake_documents.application.services.intake import IntakeContext
from serdial21.modules.locks.domain.entities import (
    AccountLock, AccountLockedError, EffectOperation, LockScope, create_lock, release_lock,
)
from serdial21.modules.rules.domain.entities import AccountingRuleVersion, RuleSetRelease
from serdial21.modules.workflow.adapters.outbound.persistence.journeys import JourneyCheckpointModel, SqlAlchemyJourneyRepository
from serdial21.modules.workflow.application.journey import (
    Journey, JourneyCommand, JourneyConflictError, JourneyNotReadyError,
    JourneyUnavailableError, PostingPolicy, PreparationPlan,
)
from serdial21.modules.workflow.domain.entities import WorkflowVersion
from serdial21.shared_kernel.observability import MetricsRegistry

NOW = datetime(2026, 9, 6, 12, tzinfo=UTC)
FIXTURE = Path(__file__).parents[1] / 'fixtures/nfe55/valid_minimal.xml'
CONFIG = ConnectorConfiguration(None, None, None)


@dataclass
class SyntheticCatalog:
    """Exclusivo do teste: não existe catálogo padrão em produção."""
    plan: PreparationPlan | None
    current_locks: tuple[AccountLock, ...] = ()

    def preparation(self, tenant_id: UUID, company_id: UUID) -> PreparationPlan | None:
        if self.plan and (self.plan.ledger.tenant_id, self.plan.ledger.company_id) != (tenant_id, company_id):
            return None
        return self.plan

    def locks(self, tenant_id: UUID, company_id: UUID) -> tuple[AccountLock, ...]:
        return tuple(lock for lock in self.current_locks if (lock.tenant_id, lock.company_id) == (tenant_id, company_id))


@dataclass
class Environment:
    session: Session
    settings: AppSettings
    tenant: UUID
    company: UUID
    proposer: UUID
    accountant: UUID
    accountant_access: UUID
    catalog: SyntheticCatalog
    metrics: MetricsRegistry

    def runtime(self):
        return create_nfe_to_dominio_runtime(
            self.session, self.settings, self.catalog, clock=lambda: NOW,
            metrics=self.metrics,
        )

    def context(self, actor: UUID | None = None) -> IntakeContext:
        return IntakeContext(self.tenant, self.company, actor or self.accountant, AuditOrigin.HUMAN, uuid4())

    def command(self) -> JourneyCommand:
        return JourneyCommand(self.tenant, self.company, self.proposer, 'synthetic-e2e',
                              date(2026, 9, 4), date(2026, 9, 1), date(2026, 9, 30), NOW + timedelta(days=1))

    def prepare(self) -> Journey:
        journey = self.runtime().prepare(self.command(), content=FIXTURE.read_bytes(), filename='synthetic.xml')
        self.session.commit()
        return journey

    def approve(self, journey: Journey, decision: str = 'APPROVED') -> Journey:
        assert journey.revision and journey.revision_hash
        # Simula submissão explícita do Contador pelo caso de uso real.
        result = self.runtime().record_decision(
            self.context(), journey.id, expected_version=journey.version,
            revision_id=journey.revision.id, revision_hash=journey.revision_hash, decision=decision,
        )
        self.session.commit()
        return result

    def export(self, journey: Journey, route_id: UUID | None = None) -> Journey:
        result = self.runtime().request_export(self.context(), journey.id, expected_version=journey.version,
                                               route_id=route_id or uuid4(), configuration=CONFIG)
        self.session.commit()
        return result


@pytest.fixture
def env(tmp_path: Path) -> Iterator[Environment]:
    settings = AppSettings(_env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:',
                           object_storage_path=tmp_path / 'evidence')
    engine = create_database_engine(settings)
    load_models()
    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    tenant, company, proposer, _ = seed_authorized_actor(session)
    accountant, membership, role, access = uuid4(), uuid4(), uuid4(), uuid4()
    with audit_scope(session, AuditContext(uuid4(), AuditOrigin.AUTOMATION, proposer, reason='synthetic E2E roles')):
        session.add(UserModel(id=accountant, provider_subject=str(accountant), display_name='Synthetic accountant', is_active=True))
        session.add(RoleModel(id=role, tenant_id=tenant, name='CONTADOR', is_active=True))
        session.flush()
        session.add(TenantMembershipModel(id=membership, tenant_id=tenant, user_id=accountant, status='active',
                                          relationship_type='employee', valid_from=NOW - timedelta(days=2), revision=1))
        session.flush()
        session.add(CompanyAccessModel(id=access, tenant_id=tenant, company_id=company, membership_id=membership,
                                        status='active', valid_from=NOW - timedelta(days=2)))
        session.add(RoleBindingModel(tenant_id=tenant, membership_id=membership, company_id=company, role_id=role,
                                      status='active', valid_from=NOW - timedelta(days=2)))
        proposer_role = session.scalar(select(RoleBindingModel.role_id).where(RoleBindingModel.tenant_id == tenant))
        for code in ('company.manage', 'journal.propose', 'journal.approve', 'journal.read', 'export.execute'):
            permission = session.scalar(select(PermissionModel).where(PermissionModel.code == code))
            if permission is None:
                permission = PermissionModel(id=uuid4(), code=code, description=code, version=1, is_active=True)
                session.add(permission)
                session.flush()
            session.add(RolePermissionModel(tenant_id=tenant, role_id=role, permission_id=permission.id))
            if code in {'journal.propose', 'journal.read', 'export.execute'}:
                session.add(RolePermissionModel(tenant_id=tenant, role_id=proposer_role, permission_id=permission.id))
        session.commit()
    accounts = tuple(AccountVersion(
        uuid4(), tenant, company, uuid4(), 1, str(index), 'SYNTHETIC ONLY', nature, balance,
        None, False, True, 'DRAFT', date(2026, 1, 1), None,
    ).publish() for index, nature, balance in ((1, 'ASSET', 'DEBIT'), (2, 'REVENUE', 'CREDIT')))
    rule = AccountingRuleVersion(
        uuid4(), tenant, company, uuid4(), 1, 'NFE55', (('model', 'EQ', '55'),), 1,
        accounts[0].id, accounts[1].id, date(2026, 1, 1), None, 'IN_REVIEW', 'SUGGEST', True, True,
    ).publish()
    release = RuleSetRelease(uuid4(), tenant, company, 'SYNTHETIC ONLY', (rule.id,), 'DRAFT').publish()
    catalog = SyntheticCatalog(PreparationPlan(
        release, (rule,), accounts,
        Ledger(uuid4(), tenant, company, 'SYNTHETIC ONLY', 'BRL', 'ACTIVE', date(2026, 1, 1), None),
        PostingPolicy(uuid4(), tenant, company, 'PUBLISHED', 'invoice_total', 2),
        WorkflowVersion(uuid4(), uuid4(), 1, 'PUBLISHED'),
        tuple((account.account_id, ()) for account in accounts),
    ))
    try:
        yield Environment(session, settings, tenant, company, proposer, accountant, access, catalog, MetricsRegistry())
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_vertical_all_internal_stages_and_reverse_trace_to_original_xml(env: Environment) -> None:
    prepared = env.prepare()
    assert prepared.status == 'PENDING_APPROVAL'
    assert prepared.evaluation and prepared.proposal and prepared.revision and prepared.item and prepared.request
    assert prepared.validation_status == 'VALID'
    assert prepared.decision is None and prepared.effect is None and prepared.batch is None
    assert sum(line.debit for line in prepared.lines) == sum(line.credit for line in prepared.lines) == Decimal('100.00')
    approved = env.approve(prepared)
    assert approved.decision.actor_id == env.accountant != env.proposer
    assert approved.effect.decision_id == approved.decision.id
    exported = env.export(approved)
    assert exported.status == exported.batch.status == 'BLOCKED_FOR_HOMOLOGATION'
    assert exported.effect.status == 'AUTHORIZED'
    # Reabre a sessão: reconstrução não depende dos objetos mantidos em memória.
    env.session.close()
    traced, original = env.runtime().trace_export(env.context(), exported.batch.id)
    assert original == FIXTURE.read_bytes()
    assert traced.imported.content_hash == __import__('hashlib').sha256(original).hexdigest()
    assert traced.proposal.source_id == traced.evaluation.id
    assert traced.sources[0].source_id == traced.imported.fiscal_document_id
    assert traced.subject.subject_id == traced.revision.id == traced.request.revision_id
    assert traced.subject.revision_hash == traced.decision.revision_hash == traced.revision_hash
    assert traced.effect.request_id == traced.request.id
    checkpoints = list(env.session.scalars(select(JourneyCheckpointModel).order_by(JourneyCheckpointModel.version)))
    assert {row.correlation_id for row in checkpoints} == {traced.correlation_id}
    assert [row.version for row in checkpoints] == list(range(1, traced.version + 1))
    audit = AuditService(SqlAlchemyAuditRepository(env.session))
    events = audit.list_by_correlation(env.tenant, traced.correlation_id)
    actions = [event.action for event in events]
    assert set(actions) >= {
        'import_batch.created', 'nfe55.imported', 'rule_evaluation.completed', 'accounting_proposal.created',
        'journal_revision.created', 'journal_revision.validated', 'work_item.created',
        'approval_request.created', 'approval_decision.recorded', 'authorized_effect.created',
        'export_batch.created', 'export_batch.blocked_for_homologation',
    }
    assert all(audit.verify_integrity(event) for event in events)
    metrics = env.metrics.snapshot()
    assert metrics['imports_total'] == metrics['proposals_total'] == metrics['approvals_total'] == 1
    assert metrics['pending_total'] == metrics['exports_total'] == 1
    # O único arquivo existente é a evidência original; nenhum TXT fictício.
    assert [path.read_bytes() for path in env.settings.object_storage_path.rglob('*') if path.is_file()] == [original]


@pytest.mark.parametrize('state', ['PENDING', 'REJECTED', 'SUPERSEDED'])
def test_nonapproved_or_superseded_revision_never_reaches_connector(env: Environment, monkeypatch, state: str) -> None:
    journey = env.prepare()
    if state == 'REJECTED':
        journey = env.approve(journey, 'REJECTED')
        assert journey.effect is None
    if state == 'SUPERSEDED':
        journey = env.approve(journey)
        journey = env.runtime().supersede(env.context(env.proposer), journey.id, expected_version=journey.version)
        env.session.commit()
    def forbidden(*_: object) -> None:
        pytest.fail('ineligible revision reached connector')
    monkeypatch.setattr(DominioConnector, 'validate_configuration', forbidden)
    with pytest.raises(JourneyNotReadyError):
        env.export(journey)
    env.session.rollback()


@pytest.mark.parametrize('scope', [LockScope.ACCOUNT, LockScope.GROUP, LockScope.MODULE, LockScope.COMPETENCE, LockScope.EXERCISE])
@pytest.mark.parametrize('operation', [EffectOperation.APPROVE, EffectOperation.EXPORT])
def test_every_lock_scope_blocks_the_critical_effect(env: Environment, scope: LockScope, operation: EffectOperation) -> None:
    plan = env.catalog.plan
    group_id = uuid4()
    env.catalog.plan = replace(plan, account_groups=tuple((a.account_id, (group_id,)) for a in plan.accounts))
    journey = env.prepare()
    if operation == EffectOperation.EXPORT:
        journey = env.approve(journey)
    targets = {
        LockScope.ACCOUNT: {'account_id': plan.accounts[0].account_id},
        LockScope.GROUP: {'group_id': group_id}, LockScope.MODULE: {'module': 'accounting'},
        LockScope.COMPETENCE: {'competence': date(2026, 9, 1)}, LockScope.EXERCISE: {'exercise': 2026},
    }
    lock = create_lock(tenant_id=env.tenant, company_id=env.company, scope=scope,
                       operations=(operation,), reason='synthetic control', **targets[scope])
    env.catalog.current_locks = (lock,)
    with pytest.raises(AccountLockedError):
        env.approve(journey) if operation == EffectOperation.APPROVE else env.export(journey)
    env.session.rollback()
    env.catalog.current_locks = (release_lock(lock, actor_id=env.accountant, reason='synthetic release', released_at=NOW),)
    with pytest.raises(JourneyNotReadyError, match='new review'):
        env.approve(journey) if operation == EffectOperation.APPROVE else env.export(journey)
    env.session.rollback()


def test_idempotency_conflict_and_unique_correlations(env: Environment) -> None:
    first = env.prepare()
    again = env.prepare()
    assert (first.id, first.version, first.correlation_id) == (again.id, again.version, again.correlation_id)
    with pytest.raises(JourneyConflictError, match='content conflict'):
        env.runtime().prepare(env.command(), content=FIXTURE.read_bytes() + b' ', filename='synthetic.xml')
    env.session.rollback()
    second = env.runtime().prepare(replace(env.command(), idempotency_key='another-journey'),
                                   content=FIXTURE.read_bytes(), filename='synthetic.xml')
    env.session.commit()
    assert second.correlation_id != first.correlation_id
    assert second.imported.artifact_id == first.imported.artifact_id


@pytest.mark.parametrize('missing', ['catalog', 'rule', 'conflict'])
def test_missing_or_ambiguous_rule_never_creates_approval(env: Environment, missing: str) -> None:
    if missing == 'catalog':
        env.catalog.plan = None
    elif missing == 'rule':
        env.catalog.plan = replace(env.catalog.plan, rules=())
    else:
        plan = env.catalog.plan
        other = replace(plan.rules[0], id=uuid4())
        env.catalog.plan = replace(plan, rules=(*plan.rules, other),
                                    release=replace(plan.release, rule_version_ids=(*plan.release.rule_version_ids, other.id)))
    journey = env.prepare()
    assert journey.status == 'PENDING_RULE'
    assert journey.proposal is journey.revision is journey.request is journey.effect is journey.batch is None


def test_quarantine_does_not_skip_to_rules(env: Environment) -> None:
    journey = env.runtime().prepare(env.command(), content=b'<not-an-nfe/>', filename='invalid.xml')
    env.session.commit()
    assert journey.status == 'QUARANTINED'
    assert journey.evaluation is journey.request is None


@pytest.mark.parametrize('invalid', ['hash', 'revision', 'stale', 'AI', 'wrong_role', 'sod', 'expired'])
def test_invalid_human_decisions_have_no_effect(env: Environment, invalid: str) -> None:
    journey = env.prepare()
    context = env.context()
    kwargs = dict(expected_version=journey.version, revision_id=journey.revision.id,
                  revision_hash=journey.revision_hash, decision='APPROVED')
    if invalid == 'hash':
        kwargs['revision_hash'] = '0' * 64
    elif invalid == 'revision':
        kwargs['revision_id'] = uuid4()
    elif invalid == 'stale':
        kwargs['expected_version'] -= 1
    elif invalid == 'AI':
        context = replace(context, origin=AuditOrigin.AI)
    elif invalid == 'wrong_role':
        context = env.context(env.proposer)
    elif invalid == 'sod':
        # O Contador também propõe, mas não pode aprovar a própria proposta.
        env.session.rollback()
        journey = env.runtime().prepare(replace(env.command(), actor_id=env.accountant, idempotency_key='sod'),
                                        content=FIXTURE.read_bytes(), filename='synthetic.xml')
        env.session.commit()
        kwargs.update(expected_version=journey.version, revision_id=journey.revision.id, revision_hash=journey.revision_hash)
    runtime = env.runtime()
    if invalid == 'expired':
        runtime._clock = lambda: NOW + timedelta(days=2)
    with pytest.raises((JourneyConflictError, PermissionError, ValueError)):
        runtime.record_decision(context, journey.id, **kwargs)
    env.session.rollback()
    assert SqlAlchemyJourneyRepository(env.session).get(env.tenant, env.company, journey.id).decision is None


@pytest.mark.parametrize('stage', ['decision', 'export', 'trace'])
def test_revoked_company_access_blocks_existing_session(env: Environment, stage: str) -> None:
    journey = env.prepare()
    if stage != 'decision':
        journey = env.approve(journey)
    if stage == 'trace':
        journey = env.export(journey)
    runtime = env.runtime()
    env.session.get(CompanyAccessModel, env.accountant_access).status = 'revoked'
    env.session.commit()
    with pytest.raises(AccessDeniedError):
        if stage == 'decision':
            runtime.record_decision(env.context(), journey.id, expected_version=journey.version,
                                    revision_id=journey.revision.id, revision_hash=journey.revision_hash, decision='APPROVED')
        elif stage == 'export':
            runtime.request_export(env.context(), journey.id, expected_version=journey.version, route_id=uuid4(), configuration=CONFIG)
        else:
            runtime.trace_export(env.context(), journey.batch.id)


def test_foreign_and_missing_exports_are_uniformly_unavailable(env: Environment) -> None:
    journey = env.export(env.approve(env.prepare()))
    # Consulta scoped não revela existência nem quando o ator possui outro escopo.
    repository = SqlAlchemyJourneyRepository(env.session)
    assert repository.find_by_export(uuid4(), env.company, journey.batch.id) is None
    assert repository.find_by_export(env.tenant, uuid4(), journey.batch.id) is None
    messages = []
    for context, batch in ((replace(env.context(), tenant_id=uuid4()), journey.batch.id),
                           (replace(env.context(), tenant_id=uuid4()), uuid4())):
        with pytest.raises(AccessDeniedError) as error:
            env.runtime().trace_export(context, batch)
        messages.append(str(error.value))
    assert messages[0] == messages[1]
    with pytest.raises(JourneyUnavailableError):
        env.runtime().trace_export(env.context(), uuid4())


def test_repeat_decision_and_stale_writer_do_not_duplicate_effect(env: Environment) -> None:
    pending = env.prepare()
    approved = env.approve(pending)
    with pytest.raises(JourneyConflictError):
        env.approve(pending)
    env.session.rollback()
    with pytest.raises(JourneyConflictError):
        SqlAlchemyJourneyRepository(env.session).append(pending.advance(status='REJECTED'))
    env.session.rollback()
    current = SqlAlchemyJourneyRepository(env.session).get(env.tenant, env.company, pending.id)
    assert current.effect.id == approved.effect.id


def test_export_retry_preserves_identity_and_conflicting_route_is_rejected(env: Environment) -> None:
    route = uuid4()
    first = env.export(env.approve(env.prepare()), route)
    again = env.export(first, route)
    assert first.batch.id == again.batch.id and first.version == again.version
    with pytest.raises(JourneyConflictError):
        env.export(again, uuid4())
    env.session.rollback()


def test_audit_failure_rolls_back_decision_and_effect(env: Environment, monkeypatch) -> None:
    pending = env.prepare()
    original = AuditService.record
    def failing(self: AuditService, record):
        if record.action == 'authorized_effect.created':
            raise RuntimeError('synthetic audit failure')
        return original(self, record)
    monkeypatch.setattr(AuditService, 'record', failing)
    with pytest.raises(RuntimeError, match='audit failure'):
        env.approve(pending)
    env.session.rollback()
    current = SqlAlchemyJourneyRepository(env.session).get(env.tenant, env.company, pending.id)
    assert current.version == pending.version and current.decision is current.effect is None
    events = AuditService(SqlAlchemyAuditRepository(env.session)).list_by_correlation(env.tenant, pending.correlation_id)
    assert not any(event.action == 'approval_decision.recorded' for event in events)


def test_checkpoint_and_original_evidence_integrity(env: Environment) -> None:
    journey = env.export(env.approve(env.prepare()))
    row = env.session.scalar(select(JourneyCheckpointModel).limit(1))
    row.status = 'TAMPERED'
    with pytest.raises(JourneyConflictError, match='immutable'):
        env.session.commit()
    env.session.rollback()
    path = next(path for path in env.settings.object_storage_path.rglob('*') if path.is_file())
    path.write_bytes(b'tampered synthetic evidence')
    with pytest.raises(ValueError, match='integrity'):
        env.runtime().trace_export(env.context(), journey.batch.id)

