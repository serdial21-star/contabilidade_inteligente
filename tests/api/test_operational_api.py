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
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.catalog.adapters.outbound.persistence.repositories import SqlAlchemyProductionCatalogRepository
from serdial21.modules.catalog.application.services.governance import CatalogGovernanceService
from serdial21.modules.catalog.domain.entities import (
    AccountSpec, CatalogSpec, MappingEntrySpec, RuleSpec, WorkflowSpec,
)
from serdial21.modules.identity.adapters.inbound.oidc import OidcJwtVerifier


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


@pytest.mark.parametrize('path', [
    'processing/00000000-0000-0000-0000-000000000001',
    'reviews',
    'reviews/00000000-0000-0000-0000-000000000001',
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
