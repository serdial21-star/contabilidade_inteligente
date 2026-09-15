from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import select

from serdial21.bootstrap.application import create_app
from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, session_scope
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel, CompanyModel, PermissionModel, RoleBindingModel, RoleModel,
    RolePermissionModel, TenantMembershipModel, TenantModel, UserModel,
)
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import SqlAlchemyAuthorizationRepository
from serdial21.modules.access_control.application.services.authorization import AuthorizationService
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.adapters.outbound.persistence.repositories import SqlAlchemyAuditRepository
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.catalog.adapters.outbound.persistence.repositories import SqlAlchemyProductionCatalogRepository
from serdial21.modules.catalog.application.services.governance import CatalogGovernanceService
from serdial21.modules.catalog.domain.entities import (
    AccountSpec, CatalogSpec, MappingEntrySpec, RuleSpec, WorkflowSpec,
)
from serdial21.modules.identity.adapters.inbound.oidc import OidcJwtVerifier
from serdial21.modules.locks.adapters.outbound.persistence.repositories import (
    SQLAlchemyAccountLockRepository,
)
from serdial21.modules.locks.domain.entities import (
    EffectOperation, LockScope, create_lock,
)
from serdial21.modules.workflow.adapters.outbound.persistence.journeys import (
    SqlAlchemyJourneyRepository,
)


ISSUER = 'https://operations.identity.test'
AUDIENCE = 'serdial21-api'
NFE = Path(__file__).parents[1] / 'fixtures/nfe55/valid_minimal.xml'
OFX = b'''<?xml version="1.0" encoding="UTF-8"?>
<OFX VERSION="2.0"><BANKMSGSRSV1><STMTTRNRS><STMTRS>
<CURDEF>BRL</CURDEF><BANKACCTFROM><BANKID>001</BANKID><BRANCHID>1</BRANCHID>
<ACCTID>0001</ACCTID><ACCTTYPE>CHECKING</ACCTTYPE></BANKACCTFROM>
<BANKTRANLIST><DTSTART>20260901</DTSTART><DTEND>20260902</DTEND>
<STMTTRN><DTPOSTED>20260902</DTPOSTED><TRNAMT>-10.00</TRNAMT><FITID>op-1</FITID></STMTTRN>
</BANKTRANLIST><LEDGERBAL><BALAMT>90.00</BALAMT></LEDGERBAL>
</STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>'''


@dataclass(frozen=True)
class OperationalFixture:
    client: TestClient
    settings: AppSettings
    tenant: UUID
    company: UUID
    other_company: UUID
    proposer: UUID
    accountant: UUID
    private_key: rsa.RSAPrivateKey

    def token(self, subject: str, *, tenant: UUID | None = None) -> str:
        now = datetime.now(UTC)
        return jwt.encode({
            'iss': ISSUER, 'sub': subject, 'aud': AUDIENCE,
            'iat': int((now - timedelta(minutes=1)).timestamp()),
            'exp': int((now + timedelta(minutes=10)).timestamp()),
            'tenant_id': str(tenant or self.tenant),
        }, self.private_key, algorithm='RS256', headers={'kid': 'operations-key'})

    def headers(
        self, subject: str, *, content_type: str | None = None,
        filename: str | None = None, key: str | None = None,
    ) -> dict[str, str]:
        result = {'Authorization': f'Bearer {self.token(subject)}'}
        if content_type:
            result['Content-Type'] = content_type
        if filename:
            result['X-Filename'] = filename
        if key:
            result['Idempotency-Key'] = key
        return result


def _seed_authorized_actor(session: object) -> tuple[UUID, UUID, UUID]:
    tenant, company, actor = uuid4(), uuid4(), uuid4()
    membership, role, permission, access = uuid4(), uuid4(), uuid4(), uuid4()
    now = datetime.now(UTC)
    session.add_all([
        TenantModel(id=tenant, name='Pilot tenant', timezone='America/Sao_Paulo',
                    currency_code='BRL', status='active'),
        UserModel(id=actor, provider_issuer=ISSUER, provider_subject='proposer',
                  display_name='Proposer', is_active=True),
        PermissionModel(id=permission, code='company.manage',
                        description='company.manage', version=1, is_active=True),
    ])
    session.flush()
    session.add_all([
        CompanyModel(id=company, tenant_id=tenant, legal_name='Pilot company',
                     tax_identifier='12345678000195', timezone='America/Sao_Paulo',
                     currency_code='BRL', status='active',
                     valid_from=now - timedelta(days=1)),
        TenantMembershipModel(id=membership, tenant_id=tenant, user_id=actor,
                              status='active', relationship_type='employee',
                              valid_from=now - timedelta(days=1), revision=1),
        RoleModel(id=role, tenant_id=tenant, name='nfe-importer', is_active=True),
    ])
    session.flush()
    session.add_all([
        CompanyAccessModel(id=access, tenant_id=tenant, company_id=company,
                           membership_id=membership, status='active',
                           valid_from=now - timedelta(days=1)),
        RolePermissionModel(tenant_id=tenant, role_id=role, permission_id=permission),
        RoleBindingModel(tenant_id=tenant, membership_id=membership, role_id=role,
                         company_id=company, status='active',
                         valid_from=now - timedelta(days=1)),
    ])
    session.flush()
    return tenant, company, actor


def _catalog_spec() -> CatalogSpec:
    return CatalogSpec(
        name='Operational catalog', ledger_name='Operational ledger',
        currency_code='BRL', chart_name='Operational chart',
        accounts=(
            AccountSpec('asset', '1.1', 'Debit account', 'ASSET', 'DEBIT',
                        None, False, True),
            AccountSpec('revenue', '3.1', 'Credit account', 'REVENUE', 'CREDIT',
                        None, False, True),
        ),
        rules=(RuleSpec(
            'nfe55', 'NF-e rule', 'NFE55', (('model', 'EQ', '55'),), 10,
            'asset', 'revenue', 'SUGGEST', True,
        ),),
        mapping_name='Operational mapping', mapping_namespace='NFE55',
        mappings=(MappingEntrySpec(
            'nfe55-asset', 10, 'asset', canonical_entity='FiscalDocument',
        ),),
        workflow=WorkflowSpec('Accounting review', 'CONTADOR', 'CONTADOR'),
        amount_field='invoice_total', decimal_places=2,
        valid_from=date(2026, 1, 1), valid_to=None,
    )


@pytest.fixture
def operational(tmp_path: Path) -> OperationalFixture:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings = AppSettings(
        _env_file=None, environment='test', database_url='sqlite+pysqlite:///:memory:',
        object_storage_path=tmp_path / 'evidence', oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE, oidc_jwks_url=f'{ISSUER}/jwks.json',
        nfe_max_xml_bytes=1024 * 1024, document_max_upload_bytes=1024 * 1024,
    )
    app = create_app(settings)
    app.state.oidc_verifier = OidcJwtVerifier(
        issuer=ISSUER, audience=AUDIENCE, jwks_url=f'{ISSUER}/jwks.json',
        leeway_seconds=0, signing_key_resolver=lambda _: private_key.public_key(),
    )
    load_models()
    assert app.state.database.engine is not None
    assert app.state.database.session_factory is not None
    Base.metadata.create_all(app.state.database.engine)

    with session_scope(app.state.database.session_factory) as session:
        with audit_scope(session, AuditContext(
            uuid4(), AuditOrigin.AUTOMATION, None, reason='operational base fixture',
        )):
            tenant, company, proposer = _seed_authorized_actor(session)
        proposer_membership = session.scalar(select(TenantMembershipModel).where(
            TenantMembershipModel.tenant_id == tenant,
            TenantMembershipModel.user_id == proposer,
        ))
        proposer_role = session.scalar(select(RoleBindingModel.role_id).where(
            RoleBindingModel.membership_id == proposer_membership.id,
        ))
        assert proposer_membership is not None and proposer_role is not None
        accountant, membership, role, access = uuid4(), uuid4(), uuid4(), uuid4()
        other_tenant, other_company = uuid4(), uuid4()
        with audit_scope(session, AuditContext(
            uuid4(), AuditOrigin.AUTOMATION, proposer, reason='operational API fixture',
        )):
            session.add_all([
                UserModel(id=accountant, provider_issuer=ISSUER, provider_subject='accountant',
                          display_name='Accountant', is_active=True),
                RoleModel(id=role, tenant_id=tenant, name='CONTADOR', is_active=True),
                TenantModel(id=other_tenant, name='Other tenant', timezone='UTC',
                            currency_code='BRL', status='active'),
            ])
            session.flush()
            session.add_all([
                TenantMembershipModel(
                    id=membership, tenant_id=tenant, user_id=accountant, status='active',
                    relationship_type='employee', valid_from=datetime.now(UTC) - timedelta(days=1),
                    revision=1,
                ),
                CompanyModel(
                    id=other_company, tenant_id=other_tenant, legal_name='Other company',
                    tax_identifier='99999999000199', timezone='UTC', currency_code='BRL',
                    status='active', valid_from=datetime.now(UTC) - timedelta(days=1),
                ),
            ])
            session.flush()
            session.add_all([
                CompanyAccessModel(
                    id=access, tenant_id=tenant, company_id=company,
                    membership_id=membership, status='active',
                    valid_from=datetime.now(UTC) - timedelta(days=1),
                ),
                RoleBindingModel(
                    tenant_id=tenant, membership_id=membership, role_id=role,
                    company_id=company, status='active',
                    valid_from=datetime.now(UTC) - timedelta(days=1),
                ),
            ])
            for code in (
                'company.read', 'journal.propose', 'journal.read',
                'journal.approve', 'audit.read', 'catalog.manage', 'catalog.review',
            ):
                permission = session.scalar(select(PermissionModel).where(
                    PermissionModel.code == code,
                ))
                if permission is None:
                    permission = PermissionModel(
                        id=uuid4(), code=code, description=code, version=1, is_active=True,
                    )
                    session.add(permission)
                    session.flush()
                if code in {'company.read', 'journal.propose', 'journal.read',
                            'catalog.manage', 'catalog.review'}:
                    session.add(RolePermissionModel(
                        tenant_id=tenant, role_id=proposer_role,
                        permission_id=permission.id,
                    ))
                if code in {'company.read', 'journal.read', 'journal.approve',
                            'audit.read', 'catalog.review'}:
                    session.add(RolePermissionModel(
                        tenant_id=tenant, role_id=role, permission_id=permission.id,
                    ))
            session.flush()

        governance = CatalogGovernanceService(
            SqlAlchemyProductionCatalogRepository(session),
            AuthorizationService(SqlAlchemyAuthorizationRepository(session)),
            AuditService(SqlAlchemyAuditRepository(session)),
        )
        correlation = uuid4()
        draft = governance.create_draft(
            tenant, company, proposer, _catalog_spec(),
            correlation_id=correlation, reason='operational catalog',
        )
        governance.submit_review(
            tenant, company, proposer, draft.id, correlation_id=correlation,
            reason='operational review',
        )
        governance.publish(
            tenant, company, accountant, draft.id, correlation_id=correlation,
            reason='operational publish',
        )

    fixture = OperationalFixture(
        TestClient(app), settings, tenant, company, other_company,
        proposer, accountant, private_key,
    )
    try:
        yield fixture
    finally:
        Base.metadata.drop_all(app.state.database.engine)
        app.state.database.dispose()


def _nfe_params() -> dict[str, str]:
    return {
        'accounting_date': '2026-09-04', 'period_start': '2026-09-01',
        'period_end': '2026-09-30',
        'approval_expires_at': (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }


def test_authenticated_nfe_review_and_approval_e2e(operational: OperationalFixture) -> None:
    correlation = str(uuid4())
    response = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(),
        headers=operational.headers(
            'proposer', content_type='application/xml', filename='document.xml', key='nfe-e2e',
        ) | {'X-Correlation-ID': correlation},
    )
    assert response.status_code == 202, response.text
    assert response.headers['x-correlation-id'] == correlation
    journey_id = response.json()['resource_id']
    assert response.json()['status'] == 'PENDING_APPROVAL'

    processing = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/processing/{journey_id}',
        headers=operational.headers('accountant'),
    )
    assert processing.status_code == 200
    assert processing.json()['kind'] == 'JOURNEY'
    reviews = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/reviews',
        headers=operational.headers('accountant'),
    )
    assert reviews.status_code == 200 and len(reviews.json()) == 1
    detail = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/reviews/{journey_id}',
        headers=operational.headers('accountant'),
    )
    assert detail.status_code == 200
    assert len(detail.json()['lines']) == 2
    assert sum(Decimal(item['debit']) for item in detail.json()['lines']) == Decimal('100.00')
    summary = detail.json()['summary']
    approved = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/reviews/{journey_id}/approve',
        headers=operational.headers('accountant') | {'Idempotency-Key': 'approve-e2e'},
        json={
            'expected_version': summary['version'],
            'revision_id': summary['revision_id'],
            'revision_hash': summary['revision_hash'],
        },
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()['status'] == 'APPROVED'
    retried = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/reviews/{journey_id}/approve',
        headers=operational.headers('accountant') | {'Idempotency-Key': 'approve-e2e'},
        json={
            'expected_version': summary['version'],
            'revision_id': summary['revision_id'],
            'revision_hash': summary['revision_hash'],
        },
    )
    assert retried.status_code == 200
    assert retried.json() == approved.json()

    audit = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/audit-events',
        headers=operational.headers('accountant'),
    )
    assert audit.status_code == 200
    assert all(item['integrity_valid'] for item in audit.json())
    assert 'approval_decision.recorded' in {item['action'] for item in audit.json()}
    assert all('after' not in item and 'before' not in item for item in audit.json())


def test_nfe_idempotency_and_content_conflict(operational: OperationalFixture) -> None:
    params = _nfe_params()
    headers = operational.headers(
        'proposer', content_type='application/xml', filename='same.xml', key='nfe-idempotent',
    )
    first = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=params, content=NFE.read_bytes(), headers=headers,
    )
    same = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=params, content=NFE.read_bytes(), headers=headers,
    )
    changed = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=params, content=NFE.read_bytes() + b' ', headers=headers,
    )
    assert first.status_code == same.status_code == 202
    assert first.json()['resource_id'] == same.json()['resource_id']
    assert changed.status_code == 409
    assert changed.json() == {'detail': 'operation conflict'}


def test_ofx_idempotency_exception_query_and_file_validation(
    operational: OperationalFixture,
) -> None:
    url = f'/api/v1/operations/companies/{operational.company}/imports/ofx'
    headers = operational.headers(
        'proposer', content_type='application/x-ofx', filename='statement.ofx', key='ofx-1',
    )
    first = operational.client.post(url, content=OFX, headers=headers)
    same = operational.client.post(url, content=OFX, headers=headers)
    changed = operational.client.post(url, content=OFX.replace(b'90.00', b'91.00'), headers=headers)
    assert first.status_code == same.status_code == 202
    assert first.json()['resource_id'] == same.json()['resource_id']
    assert changed.status_code == 409

    invalid = operational.client.post(
        url, content=b'not-ofx', headers=operational.headers(
            'proposer', content_type='application/x-ofx', filename='bad.ofx', key='ofx-bad',
        ),
    )
    assert invalid.status_code == 202 and invalid.json()['status'] == 'QUARANTINED'
    issues = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/exceptions',
        headers=operational.headers('proposer'),
    )
    assert issues.status_code == 200
    assert issues.json()[0]['code'] == 'UNSUPPORTED_OFX'
    assert 'message' not in issues.json()[0]

    wrong_type = operational.client.post(
        url, content=OFX, headers=operational.headers(
            'proposer', content_type='application/octet-stream', filename='statement.ofx', key='wrong-type',
        ),
    )
    wrong_name = operational.client.post(
        url, content=OFX, headers=operational.headers(
            'proposer', content_type='application/x-ofx', filename='../statement.ofx', key='wrong-name',
        ),
    )
    too_large = operational.client.post(
        url, content=b'x' * (operational.settings.document_max_upload_bytes + 1),
        headers=operational.headers(
            'proposer', content_type='application/x-ofx', filename='large.ofx', key='large',
        ),
    )
    assert wrong_type.status_code == 415
    assert wrong_name.status_code == 422
    assert too_large.status_code == 413


def test_company_and_document_read_projections_are_scoped_and_minimized(
    operational: OperationalFixture,
) -> None:
    upload = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/ofx',
        content=OFX, headers=operational.headers(
            'proposer', content_type='application/x-ofx',
            filename='<img onerror=alert(1)>.ofx', key='document-projection',
        ),
    )
    assert upload.status_code == 202, upload.text

    company = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}',
        headers=operational.headers('proposer'),
    )
    assert company.status_code == 200
    assert company.json()['legal_name'] == 'Pilot company'
    assert 'tenant_id' not in company.json()

    page = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/documents',
        params={'search': '<img', 'source': 'OFX_OPERATIONAL', 'status': 'COMPLETED', 'limit': 10},
        headers=operational.headers('proposer'),
    )
    assert page.status_code == 200, page.text
    assert page.json()['total'] == 1
    assert page.json()['items'][0]['filename'] == '<img onerror=alert(1)>.ofx'
    assert 'artifact_id' not in page.json()['items'][0]
    assert 'storage_key' not in page.json()['items'][0]
    document_id = page.json()['items'][0]['id']

    detail = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/documents/{document_id}',
        headers=operational.headers('proposer'),
    )
    assert detail.status_code == 200
    assert detail.json()['document']['processing_status'] == 'COMPLETED'
    assert detail.json()['issues'] == []

    summary = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/documents/summary',
        headers=operational.headers('proposer'),
    )
    assert summary.status_code == 200
    assert summary.json() == {'received': 1, 'processed': 1, 'attention_required': 0}


def test_document_idor_and_invalid_filters_are_safe(
    operational: OperationalFixture,
) -> None:
    own = f'/api/v1/operations/companies/{operational.company}/documents/{uuid4()}'
    cross = f'/api/v1/operations/companies/{operational.other_company}/documents/{uuid4()}'
    missing = operational.client.get(own, headers=operational.headers('proposer'))
    cross_tenant = operational.client.get(cross, headers=operational.headers('proposer'))
    invalid_range = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/documents',
        params={'received_from': '2026-09-10', 'received_to': '2026-09-01'},
        headers=operational.headers('proposer'),
    )
    assert missing.status_code == 404
    assert missing.json() == {'detail': 'resource unavailable'}
    assert cross_tenant.status_code == 403
    assert cross_tenant.json() == {'detail': 'access denied'}
    assert invalid_range.status_code == 422
    assert invalid_range.json() == {'detail': 'invalid operation'}


def test_fiscal_projection_lists_structured_nfe_items_and_document_link(
    operational: OperationalFixture,
) -> None:
    imported = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(), headers=operational.headers(
            'proposer', content_type='application/xml', filename='fiscal-phase07.xml',
            key='fiscal-phase07',
        ),
    )
    assert imported.status_code == 202, imported.text
    listing = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/fiscal-documents',
        params={'search': 'Emitente', 'status': 'REPORTED_AUTHORIZED', 'limit': 10},
        headers=operational.headers('proposer'),
    )
    assert listing.status_code == 200, listing.text
    assert listing.json()['total'] == 1
    summary = listing.json()['items'][0]
    assert summary['model'] == '55'
    assert summary['document_receipt_id'] is not None
    assert 'artifact_id' not in summary and 'source_hash' not in summary

    detail = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/fiscal-documents/{summary['id']}",
        headers=operational.headers('proposer'),
    )
    assert detail.status_code == 200
    assert detail.json()['item_count'] == len(detail.json()['items']) == 1
    assert detail.json()['items'][0]['cfop'] == '5102'
    assert {item['tax_type'] for item in detail.json()['tax_totals']} >= {'ICMS', 'PIS', 'COFINS'}
    document = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/documents/{summary['document_receipt_id']}",
        headers=operational.headers('proposer'),
    )
    assert document.status_code == 200
    assert document.json()['fiscal_document_id'] == summary['id']
    assert document.json()['bank_statement_id'] is None


def test_financial_projection_masks_account_and_preserves_credit_debit(
    operational: OperationalFixture,
) -> None:
    credit = b'<STMTTRN><DTPOSTED>20260902</DTPOSTED><TRNAMT>15.00</TRNAMT><FITID>op-credit</FITID><MEMO>Credito sintetico</MEMO></STMTTRN>'
    content = OFX.replace(b'</BANKTRANLIST>', credit + b'</BANKTRANLIST>')
    imported = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/ofx',
        content=content, headers=operational.headers(
            'proposer', content_type='application/x-ofx', filename='financial-phase07.ofx',
            key='financial-phase07',
        ),
    )
    assert imported.status_code == 202, imported.text
    listing = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/bank-statements',
        headers=operational.headers('proposer'),
    )
    assert listing.status_code == 200
    statement = listing.json()['items'][0]
    assert statement['account_masked'].startswith('••••')
    assert statement['account_masked'] != '0001'
    assert 'account_number' not in statement and 'artifact_id' not in statement

    detail = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/bank-statements/{statement['id']}",
        headers=operational.headers('proposer'),
    )
    assert detail.status_code == 200
    transactions = detail.json()['transactions']['items']
    assert {(item['direction'], Decimal(item['amount'])) for item in transactions} == {
        ('DEBIT', Decimal('-10.00')), ('CREDIT', Decimal('15.00')),
    }
    credits = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/bank-statements/{statement['id']}",
        params={'direction': 'CREDIT', 'search': 'sintetico'},
        headers=operational.headers('proposer'),
    )
    assert credits.status_code == 200
    assert credits.json()['transactions']['total'] == 1
    document = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/documents/{statement['document_receipt_id']}",
        headers=operational.headers('proposer'),
    )
    assert document.status_code == 200
    assert document.json()['bank_statement_id'] == statement['id']
    assert document.json()['fiscal_document_id'] is None


def test_accounting_intelligence_projects_exact_proposal_rule_and_evidence(
    operational: OperationalFixture,
) -> None:
    imported = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(), headers=operational.headers(
            'proposer', content_type='application/xml', filename='accounting-phase08.xml',
            key='accounting-phase08',
        ),
    )
    assert imported.status_code == 202, imported.text
    journey_id = imported.json()['resource_id']

    listing = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/accounting-proposals',
        params={'status': 'PENDING_APPROVAL', 'offset': 0, 'limit': 10},
        headers=operational.headers('accountant'),
    )
    assert listing.status_code == 200, listing.text
    assert listing.json()['total'] == 1
    summary = listing.json()['items'][0]
    assert summary['journey_id'] == journey_id
    assert summary['rule_name'] == 'NF-e rule'
    assert Decimal(summary['total_debit']) == Decimal('100.00')
    assert Decimal(summary['total_credit']) == Decimal('100.00')
    assert summary['balanced'] is True
    assert summary['status'] == 'PENDING_APPROVAL'
    assert 'tenant_id' not in summary

    detail = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/accounting-proposals/{journey_id}',
        headers=operational.headers('accountant'),
    )
    assert detail.status_code == 200, detail.text
    payload = detail.json()
    assert len(payload['lines']) == 2
    assert payload['rule']['conditions'] == [
        {'field': 'model', 'operator': 'EQ', 'value': '55'},
    ]
    assert payload['rule']['debit_account_code'] == '1.1'
    assert payload['rule']['credit_account_code'] == '3.1'
    assert payload['sources'][0]['source_type'] == 'FiscalDocument'
    assert payload['sources'][0]['document_receipt_id'] is not None
    assert 'raw_payload' not in payload['sources'][0]

    activity = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/accounting-proposals/{journey_id}/activity',
        headers=operational.headers('accountant'),
    )
    assert activity.status_code == 200
    assert all(item['integrity_valid'] for item in activity.json())

    catalog = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/accounting-catalog',
        params={'effective_at': '2026-09-04'},
        headers=operational.headers('proposer'),
    )
    assert catalog.status_code == 200, catalog.text
    assert catalog.json()['decimal_places'] == 2
    rule_id = catalog.json()['rules'][0]['id']
    account_id = catalog.json()['accounts'][0]['id']
    assert operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/accounting-rules/{rule_id}',
        params={'effective_at': '2026-09-04'},
        headers=operational.headers('proposer'),
    ).status_code == 200
    assert operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/accounting-accounts/{account_id}',
        params={'effective_at': '2026-09-04'},
        headers=operational.headers('proposer'),
    ).status_code == 200


def test_decision_line_golden_approval_is_read_only_minimized_and_idempotent(
    operational: OperationalFixture,
) -> None:
    imported = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(), headers=operational.headers(
            'proposer', content_type='application/xml', filename='trace.xml',
            key='trace-golden',
        ),
    ).json()
    journey_id = imported['resource_id']
    review = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/reviews/{journey_id}',
        headers=operational.headers('accountant'),
    ).json()['summary']
    payload = {
        'expected_version': review['version'], 'revision_id': review['revision_id'],
        'revision_hash': review['revision_hash'],
    }
    url = f'/api/v1/operations/companies/{operational.company}/reviews/{journey_id}/approve'
    headers = operational.headers('accountant') | {'Idempotency-Key': 'trace-approve'}
    first = operational.client.post(url, headers=headers, json=payload)
    retry = operational.client.post(url, headers=headers, json=payload)
    assert first.status_code == retry.status_code == 200

    trace_url = f'/api/v1/operations/companies/{operational.company}/decision-lines/ACCOUNTING_PROPOSAL/{journey_id}'
    response = operational.client.get(trace_url, headers=operational.headers('accountant'))
    assert response.status_code == 200, response.text
    trace = response.json()
    assert trace['root_status'] == 'APPROVED'
    assert [event['occurred_at'] for event in trace['events']] == sorted(
        event['occurred_at'] for event in trace['events']
    )
    approvals = [event for event in trace['events'] if event['title'] == 'Proposta aprovada']
    categories = {event['category'] for event in trace['events']}
    assert {'PROCESSING', 'RULE', 'PROPOSAL', 'REVIEW', 'APPROVAL'} <= categories
    rule = next(event for event in trace['events'] if event['category'] == 'RULE')
    proposal = next(event for event in trace['events'] if event['title'] == 'Proposta contábil criada')
    assert rule['title'] == 'Regra aplicada: NF-e rule'
    assert 'selecionada deterministicamente por prioridade' in rule['description']
    assert 'débito total 100.00' in proposal['description']
    assert 'crédito total 100.00' in proposal['description']
    assert len(approvals) == 1
    assert approvals[0]['actor_display_name'] == 'Accountant'
    assert approvals[0]['actor_kind'] == 'PROFESSIONAL_ACTION'
    serialized = response.text.lower()
    assert all(term not in serialized for term in (
        'actor_id', 'tenant_id', 'correlation_id', 'before_state', 'after_state',
        'revision_hash', '@', '<nfe', 'storage_key',
    ))
    assert operational.client.post(
        trace_url, headers=operational.headers('accountant'),
    ).status_code == 405

    proposal = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/accounting-proposals/{journey_id}',
        headers=operational.headers('accountant'),
    ).json()
    source = proposal['sources'][0]
    for root_type, root_id in (
        ('FISCAL_DOCUMENT', source['source_id']),
        ('DOCUMENT', source['document_receipt_id']),
    ):
        source_trace = operational.client.get(
            f'/api/v1/operations/companies/{operational.company}/decision-lines/{root_type}/{root_id}',
            headers=operational.headers('accountant'),
        )
        assert source_trace.status_code == 200, source_trace.text
        source_events = source_trace.json()['events']
        assert any(
            event['title'] == 'Regra aplicada: NF-e rule'
            for event in source_events
        )
        professional_approvals = [
            event for event in source_events
            if event['title'] == 'Proposta aprovada'
            and event['actor_kind'] == 'PROFESSIONAL_ACTION'
        ]
        assert len(professional_approvals) == 1


def test_decision_line_does_not_follow_same_correlation_into_other_tenant(
    operational: OperationalFixture,
) -> None:
    imported = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(), headers=operational.headers(
            'proposer', content_type='application/xml', filename='source-idor.xml',
            key='source-chain-idor',
        ),
    ).json()
    session_factory = operational.client.app.state.database.session_factory
    assert session_factory is not None
    with session_scope(session_factory) as session:
        journey = SqlAlchemyJourneyRepository(session).get(
            operational.tenant, operational.company, UUID(imported['resource_id']),
        )
        other = session.scalar(select(CompanyModel).where(
            CompanyModel.id == operational.other_company,
        ))
        assert journey is not None and other is not None
        AuditService(SqlAlchemyAuditRepository(session)).record(AuditRecord(
            tenant_id=other.tenant_id, company_id=other.id, actor_id=None,
            origin=AuditOrigin.AUTOMATION, module='workflow',
            action='journey.quarantined', subject_type='NFeJourney',
            subject_id=uuid4(), subject_version=1, before=None,
            after={'status': 'QUARANTINED'}, reason=None,
            correlation_id=journey.correlation_id,
        ))

    response = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/decision-lines/ACCOUNTING_PROPOSAL/{imported['resource_id']}",
        headers=operational.headers('accountant'),
    )
    assert response.status_code == 200
    assert not any(
        event['title'] == 'Documento em quarentena'
        for event in response.json()['events']
    )


def test_decision_line_idor_and_underlying_permission_are_enforced(
    operational: OperationalFixture,
) -> None:
    resource_id = uuid4()
    own = f'/api/v1/operations/companies/{operational.company}/decision-lines/DOCUMENT/{resource_id}'
    cross = f'/api/v1/operations/companies/{operational.other_company}/decision-lines/DOCUMENT/{resource_id}'
    assert operational.client.get(own).status_code == 401
    assert operational.client.get(
        own, headers=operational.headers('accountant'),
    ).status_code == 404
    denied = operational.client.get(
        own, headers=operational.headers('proposer'),
    )
    assert denied.status_code == 403
    cross_response = operational.client.get(
        cross, headers=operational.headers('accountant'),
    )
    assert cross_response.status_code == 403


def test_decision_line_derives_current_lock_without_inventing_attempt(
    operational: OperationalFixture,
) -> None:
    imported = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(), headers=operational.headers(
            'proposer', content_type='application/xml', filename='trace-lock.xml',
            key='trace-lock',
        ),
    ).json()
    session_factory = operational.client.app.state.database.session_factory
    assert session_factory is not None
    with session_scope(session_factory) as session:
        SQLAlchemyAccountLockRepository(session).add(create_lock(
            tenant_id=operational.tenant, company_id=operational.company,
            scope=LockScope.MODULE, operations=(EffectOperation.APPROVE,),
            reason='synthetic trace lock', module='accounting',
        ))

    response = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/decision-lines/ACCOUNTING_PROPOSAL/{imported['resource_id']}",
        headers=operational.headers('accountant'),
    )
    assert response.status_code == 200, response.text
    blocks = [event for event in response.json()['events'] if event['category'] == 'BLOCK']
    assert len(blocks) == 1
    assert blocks[0]['evidence_kind'] == 'DOMAIN_DERIVED_EVENT'
    assert 'tentativa' not in blocks[0]['description'].lower()


def test_accounting_proposal_and_catalog_idor_are_safe(
    operational: OperationalFixture,
) -> None:
    paths = (
        f'accounting-proposals/{uuid4()}',
        f'accounting-rules/{uuid4()}',
        f'accounting-accounts/{uuid4()}',
    )
    for path in paths:
        unauthenticated = operational.client.get(
            f'/api/v1/operations/companies/{operational.company}/{path}',
            params={'effective_at': '2026-09-04'},
        )
        own = operational.client.get(
            f'/api/v1/operations/companies/{operational.company}/{path}',
            params={'effective_at': '2026-09-04'},
            headers=operational.headers('proposer'),
        )
        cross = operational.client.get(
            f'/api/v1/operations/companies/{operational.other_company}/{path}',
            params={'effective_at': '2026-09-04'},
            headers=operational.headers('proposer'),
        )
        assert unauthenticated.status_code == 401
        assert own.status_code == 404
        assert own.json() == {'detail': 'resource unavailable'}
        assert cross.status_code == 403
        assert cross.json() == {'detail': 'access denied'}
    catalog_cross = operational.client.get(
        f'/api/v1/operations/companies/{operational.other_company}/accounting-catalog',
        params={'effective_at': '2026-09-04'},
        headers=operational.headers('proposer'),
    )
    assert catalog_cross.status_code == 403
    assert catalog_cross.json() == {'detail': 'access denied'}
    catalog_unauthenticated = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/accounting-catalog',
        params={'effective_at': '2026-09-04'},
    )
    assert catalog_unauthenticated.status_code == 401


@pytest.mark.parametrize('resource', ['fiscal-documents', 'bank-statements'])
def test_fiscal_and_financial_idor_are_uniform(
    operational: OperationalFixture, resource: str,
) -> None:
    own_missing = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/{resource}/{uuid4()}',
        headers=operational.headers('proposer'),
    )
    cross_tenant = operational.client.get(
        f'/api/v1/operations/companies/{operational.other_company}/{resource}/{uuid4()}',
        headers=operational.headers('proposer'),
    )
    assert own_missing.status_code == 404
    assert own_missing.json() == {'detail': 'resource unavailable'}
    assert cross_tenant.status_code == 403
    assert cross_tenant.json() == {'detail': 'access denied'}


@pytest.mark.parametrize('path', [
    '',
    'documents',
    'documents/summary',
    'documents/00000000-0000-0000-0000-000000000001',
    'fiscal-documents',
    'fiscal-documents/00000000-0000-0000-0000-000000000001',
    'bank-statements',
    'bank-statements/00000000-0000-0000-0000-000000000001',
    'processing/00000000-0000-0000-0000-000000000001',
    'reviews',
    'reviews/00000000-0000-0000-0000-000000000001',
    'accounting-proposals',
    'accounting-proposals/00000000-0000-0000-0000-000000000001',
    'exceptions',
    'audit-events',
])
def test_read_endpoints_require_authentication_and_hide_cross_tenant_company(
    operational: OperationalFixture, path: str,
) -> None:
    own_url = f'/api/v1/operations/companies/{operational.company}/{path}'
    cross_url = f'/api/v1/operations/companies/{operational.other_company}/{path}'
    unauthenticated = operational.client.get(own_url)
    cross_tenant = operational.client.get(
        cross_url, headers=operational.headers('proposer'),
    )
    unknown = operational.client.get(
        f'/api/v1/operations/companies/{uuid4()}/{path}',
        headers=operational.headers('proposer'),
    )
    assert unauthenticated.status_code == 401
    assert cross_tenant.status_code == unknown.status_code == 403
    assert cross_tenant.json() == unknown.json() == {'detail': 'access denied'}


def test_insufficient_role_cannot_decide_and_reject_is_available(
    operational: OperationalFixture,
) -> None:
    imported = operational.client.post(
        f'/api/v1/operations/companies/{operational.company}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(), headers=operational.headers(
            'proposer', content_type='application/xml', filename='decision.xml', key='decision',
        ),
    ).json()
    detail = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/reviews/{imported['resource_id']}",
        headers=operational.headers('proposer'),
    ).json()['summary']
    payload = {
        'expected_version': detail['version'], 'revision_id': detail['revision_id'],
        'revision_hash': detail['revision_hash'],
    }
    denied = operational.client.post(
        f"/api/v1/operations/companies/{operational.company}/reviews/{imported['resource_id']}/approve",
        headers=operational.headers('proposer') | {'Idempotency-Key': 'denied-decision'}, json=payload,
    )
    rejected = operational.client.post(
        f"/api/v1/operations/companies/{operational.company}/reviews/{imported['resource_id']}/reject",
        headers=operational.headers('accountant') | {'Idempotency-Key': 'reject-decision'}, json=payload,
    )
    assert denied.status_code == 403
    assert rejected.status_code == 200 and rejected.json()['status'] == 'REJECTED'
    trace = operational.client.get(
        f"/api/v1/operations/companies/{operational.company}/decision-lines/REVIEW/{imported['resource_id']}",
        headers=operational.headers('accountant'),
    )
    assert trace.status_code == 200
    assert any(event['category'] == 'REJECTION' for event in trace.json()['events'])
    assert 'REJECTION_REASON_NOT_AVAILABLE' in trace.json()['data_gaps']


def test_audit_endpoint_requires_audit_permission(operational: OperationalFixture) -> None:
    response = operational.client.get(
        f'/api/v1/operations/companies/{operational.company}/audit-events',
        headers=operational.headers('proposer'),
    )
    assert response.status_code == 403
    assert response.json() == {'detail': 'access denied'}


def test_import_endpoints_require_authentication_permission_and_company_scope(
    operational: OperationalFixture,
) -> None:
    own = f'/api/v1/operations/companies/{operational.company}/imports/ofx'
    cross = f'/api/v1/operations/companies/{operational.other_company}/imports/ofx'
    upload_headers = {
        'Content-Type': 'application/x-ofx', 'X-Filename': 'statement.ofx',
        'Idempotency-Key': 'authorization-check',
    }
    unauthenticated = operational.client.post(own, content=OFX, headers=upload_headers)
    insufficient = operational.client.post(
        own, content=OFX,
        headers=operational.headers(
            'accountant', content_type='application/x-ofx',
            filename='statement.ofx', key='authorization-check',
        ),
    )
    cross_tenant = operational.client.post(
        cross, content=OFX,
        headers=operational.headers(
            'proposer', content_type='application/x-ofx',
            filename='statement.ofx', key='authorization-check',
        ),
    )
    unknown = operational.client.post(
        f'/api/v1/operations/companies/{uuid4()}/imports/ofx', content=OFX,
        headers=operational.headers(
            'proposer', content_type='application/x-ofx',
            filename='statement.ofx', key='authorization-check',
        ),
    )
    assert unauthenticated.status_code == 401
    assert insufficient.status_code == cross_tenant.status_code == unknown.status_code == 403
    assert insufficient.json() == cross_tenant.json() == unknown.json() == {
        'detail': 'access denied',
    }


def test_nfe_import_rejects_cross_tenant_and_unknown_company_uniformly(
    operational: OperationalFixture,
) -> None:
    cross_tenant = operational.client.post(
        f'/api/v1/operations/companies/{operational.other_company}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(), headers=operational.headers(
            'proposer', content_type='application/xml', filename='isolated.xml',
            key='nfe-company-isolation',
        ),
    )
    unknown = operational.client.post(
        f'/api/v1/operations/companies/{uuid4()}/imports/nfe',
        params=_nfe_params(), content=NFE.read_bytes(), headers=operational.headers(
            'proposer', content_type='application/xml', filename='isolated.xml',
            key='nfe-company-isolation',
        ),
    )
    assert cross_tenant.status_code == unknown.status_code == 403
    assert cross_tenant.json() == unknown.json() == {'detail': 'access denied'}
