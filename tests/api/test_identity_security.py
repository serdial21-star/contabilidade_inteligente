from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import Base, session_scope
from serdial21.bootstrap.application import create_app
from serdial21.bootstrap.model_registry import load_models
from serdial21.bootstrap.settings import AppSettings
from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel,
    CompanyModel,
    PermissionModel,
    RoleBindingModel,
    RoleModel,
    RolePermissionModel,
    TenantMembershipModel,
    TenantModel,
    UserModel,
)
from serdial21.modules.audit.adapters.outbound.persistence.models import AuditEventModel
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.identity.adapters.inbound.oidc import OidcJwtVerifier


ISSUER = 'https://identity.example.test'
AUDIENCE = 'serdial21-api'
NOW = datetime.now(UTC).replace(microsecond=0)


@dataclass(frozen=True)
class IdentityFixture:
    app: FastAPI
    tenant_a: UUID
    tenant_b: UUID
    company_a: UUID
    company_b: UUID
    actor_id: UUID
    actor_membership_id: UUID
    target_role_id: UUID
    private_key: rsa.RSAPrivateKey

    def token(
        self,
        *,
        subject: str = 'actor-subject',
        tenant_id: UUID | None = None,
        expired: bool = False,
        signing_key: rsa.RSAPrivateKey | None = None,
    ) -> str:
        issued = NOW - timedelta(minutes=2)
        expires = NOW - timedelta(minutes=1) if expired else NOW + timedelta(minutes=10)
        return jwt.encode(
            {
                'iss': ISSUER,
                'sub': subject,
                'aud': AUDIENCE,
                'iat': int(issued.timestamp()),
                'exp': int(expires.timestamp()),
                'tenant_id': str(tenant_id or self.tenant_a),
            },
            signing_key or self.private_key,
            algorithm='RS256',
            headers={'kid': 'test-key'},
        )


@pytest.fixture
def identity() -> IdentityFixture:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings = AppSettings(
        _env_file=None,
        environment='test',
        database_url='sqlite+pysqlite:///:memory:',
        oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE,
        oidc_jwks_url=f'{ISSUER}/jwks.json',
    )
    app = create_app(settings)
    app.state.oidc_verifier = OidcJwtVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url=f'{ISSUER}/jwks.json',
        leeway_seconds=0,
        signing_key_resolver=lambda _: private_key.public_key(),
    )
    load_models()
    assert app.state.database.engine is not None
    assert app.state.database.session_factory is not None
    Base.metadata.create_all(app.state.database.engine)

    tenant_a, tenant_b, company_a, company_b = (uuid4() for _ in range(4))
    actor_id, actor_membership_id = uuid4(), uuid4()
    admin_role_id, target_role_id = uuid4(), uuid4()
    identity_permission_id, read_permission_id = uuid4(), uuid4()
    with session_scope(app.state.database.session_factory) as session:
        with audit_scope(session, AuditContext(
            correlation_id=uuid4(), origin=AuditOrigin.AUTOMATION,
            actor_id=actor_id, reason='identity API fixture',
        )):
            session.add_all([
                TenantModel(id=tenant_a, name='Tenant A', timezone='America/Sao_Paulo', currency_code='BRL', status='active'),
                TenantModel(id=tenant_b, name='Tenant B', timezone='America/Sao_Paulo', currency_code='BRL', status='active'),
                UserModel(id=actor_id, provider_issuer=ISSUER, provider_subject='actor-subject', display_name='Actor', is_active=True),
                PermissionModel(id=identity_permission_id, code='identity.manage', description='identity.manage', version=1, is_active=True),
                PermissionModel(id=read_permission_id, code='company.read', description='company.read', version=1, is_active=True),
            ])
            session.flush()
            session.add_all([
                TenantMembershipModel(id=actor_membership_id, tenant_id=tenant_a, user_id=actor_id, status='active', relationship_type='employee', valid_from=NOW - timedelta(days=1), revision=1),
                CompanyModel(id=company_a, tenant_id=tenant_a, legal_name='Company A', tax_identifier='10000000000001', timezone='America/Sao_Paulo', currency_code='BRL', status='active', valid_from=NOW - timedelta(days=1)),
                CompanyModel(id=company_b, tenant_id=tenant_b, legal_name='Company B', tax_identifier='20000000000001', timezone='America/Sao_Paulo', currency_code='BRL', status='active', valid_from=NOW - timedelta(days=1)),
                RoleModel(id=admin_role_id, tenant_id=tenant_a, name='identity-admin', is_active=True),
                RoleModel(id=target_role_id, tenant_id=tenant_a, name='company-reader', is_active=True),
            ])
            session.flush()
            session.add_all([
                RolePermissionModel(tenant_id=tenant_a, role_id=admin_role_id, permission_id=identity_permission_id),
                RolePermissionModel(tenant_id=tenant_a, role_id=target_role_id, permission_id=read_permission_id),
                RoleBindingModel(tenant_id=tenant_a, membership_id=actor_membership_id, role_id=admin_role_id, company_id=None, status='active', valid_from=NOW - timedelta(days=1)),
            ])
            session.flush()

    fixture = IdentityFixture(
        app, tenant_a, tenant_b, company_a, company_b, actor_id,
        actor_membership_id, target_role_id, private_key,
    )
    try:
        yield fixture
    finally:
        Base.metadata.drop_all(app.state.database.engine)
        app.state.database.dispose()


def _headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def _onboard(client: TestClient, identity: IdentityFixture) -> tuple[UUID, str]:
    response = client.post(
        '/api/v1/identity/onboarding',
        headers=_headers(identity.token()),
        json={
            'provider_subject': 'target-subject',
            'display_name': 'Target User',
            'email': 'target@example.test',
            'relationship_type': 'employee',
            'company_ids': [str(identity.company_a)],
            'role_id': str(identity.target_role_id),
            'reason': 'approved onboarding',
        },
    )
    assert response.status_code == 201, response.json()
    return UUID(response.json()['user_id']), identity.token(subject='target-subject')


def test_onboarding_context_offboarding_and_audit(identity: IdentityFixture) -> None:
    client = TestClient(identity.app)
    target_user_id, target_token = _onboard(client, identity)
    context = client.get(
        '/api/v1/identity/context',
        headers=_headers(target_token),
        params={'company_id': str(identity.company_a)},
    )
    assert context.status_code == 200
    assert context.json()['tenant_id'] == str(identity.tenant_a)
    assert context.json()['company_id'] == str(identity.company_a)
    assert context.json()['permission'] == 'company.read'

    offboard = client.post(
        f'/api/v1/identity/users/{target_user_id}/offboard',
        headers=_headers(identity.token()),
        json={'reason': 'approved offboarding'},
    )
    assert offboard.status_code == 200
    assert offboard.json() == {'status': 'revoked', 'user_deactivated': True}
    denied = client.get(
        '/api/v1/identity/context',
        headers=_headers(target_token),
        params={'company_id': str(identity.company_a)},
    )
    assert denied.status_code == 403
    assert denied.json() == {'detail': 'access denied'}

    assert identity.app.state.database.session_factory is not None
    with session_scope(identity.app.state.database.session_factory) as session:
        user = session.get(UserModel, target_user_id)
        assert user is not None and user.is_active is False
        membership = session.scalar(select(TenantMembershipModel).where(TenantMembershipModel.user_id == target_user_id))
        assert membership is not None and membership.status == 'revoked'
        assert all(item.status == 'revoked' for item in session.scalars(select(CompanyAccessModel).where(CompanyAccessModel.membership_id == membership.id)))
        assert all(item.status == 'revoked' for item in session.scalars(select(RoleBindingModel).where(RoleBindingModel.membership_id == membership.id)))
        actions = set(session.scalars(select(AuditEventModel.action).where(
            AuditEventModel.tenant_id == identity.tenant_a,
            AuditEventModel.module == 'identity',
        )))
        assert actions == {'identity.onboarded', 'identity.offboarded'}


def test_invalid_and_expired_tokens_have_same_safe_response(identity: IdentityFixture) -> None:
    client = TestClient(identity.app)
    untrusted_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    invalid = client.get('/api/v1/identity/context', headers=_headers(identity.token(signing_key=untrusted_key)), params={'company_id': str(identity.company_a)})
    expired = client.get('/api/v1/identity/context', headers=_headers(identity.token(expired=True)), params={'company_id': str(identity.company_a)})
    assert invalid.status_code == expired.status_code == 401
    assert invalid.json() == expired.json() == {'detail': 'authentication failed'}


def test_cross_tenant_and_unknown_company_do_not_leak_existence(identity: IdentityFixture) -> None:
    client = TestClient(identity.app)
    tenant_b = client.get('/api/v1/identity/context', headers=_headers(identity.token(tenant_id=identity.tenant_b)), params={'company_id': str(identity.company_b)})
    company_b = client.get('/api/v1/identity/context', headers=_headers(identity.token()), params={'company_id': str(identity.company_b)})
    unknown = client.get('/api/v1/identity/context', headers=_headers(identity.token()), params={'company_id': str(uuid4())})
    assert tenant_b.status_code == company_b.status_code == unknown.status_code == 403
    assert tenant_b.json() == company_b.json() == unknown.json() == {'detail': 'access denied'}


@pytest.mark.parametrize('revocation', ['user', 'membership', 'role', 'company_access'])
def test_each_internal_access_boundary_is_revalidated(
    identity: IdentityFixture,
    revocation: str,
) -> None:
    client = TestClient(identity.app)
    target_user_id, target_token = _onboard(client, identity)
    assert identity.app.state.database.session_factory is not None
    with session_scope(identity.app.state.database.session_factory) as session:
        membership = session.scalar(select(TenantMembershipModel).where(TenantMembershipModel.user_id == target_user_id))
        assert membership is not None
        with audit_scope(session, AuditContext(
            correlation_id=uuid4(), origin=AuditOrigin.AUTOMATION,
            actor_id=identity.actor_id, reason='negative access test',
        )):
            if revocation == 'user':
                user = session.get(UserModel, target_user_id)
                assert user is not None
                user.is_active = False
            elif revocation == 'membership':
                membership.status = 'revoked'
                membership.revision += 1
            elif revocation == 'role':
                binding = session.scalar(select(RoleBindingModel).where(RoleBindingModel.membership_id == membership.id))
                assert binding is not None
                binding.status = 'revoked'
            else:
                access = session.scalar(select(CompanyAccessModel).where(CompanyAccessModel.membership_id == membership.id))
                assert access is not None
                access.status = 'revoked'
            session.flush()
    response = client.get('/api/v1/identity/context', headers=_headers(target_token), params={'company_id': str(identity.company_a)})
    assert response.status_code == 403
    assert response.json() == {'detail': 'access denied'}
