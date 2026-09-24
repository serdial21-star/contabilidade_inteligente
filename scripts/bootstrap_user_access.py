'''Provisiona um usuário do Sistema B para a ponte de login do Sistema A (ADR 0014).

Idempotente: rodar de novo com os mesmos argumentos não duplica nada. Concede
acesso de leitura a TODAS as empresas do tenant informado — cenário de um
único escritório (ver ADR 0014); não decide papéis granulares por pessoa.
'''

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from serdial21.bootstrap.audit import AuditContext, audit_scope
from serdial21.bootstrap.database import create_database_engine, create_session_factory
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
    UserModel,
)
from serdial21.modules.audit.domain.entities import AuditOrigin


DEFAULT_PERMISSIONS = ('company.read', 'journal.read', 'audit.read')
DEFAULT_ROLE_NAME = 'Leitura operacional (ponte Sistema A)'
ACTIVE = 'active'


def _find_or_create_user(
    session: Session, *, issuer: str, subject: str, display_name: str, email: str | None,
) -> UserModel:
    user = session.scalar(select(UserModel).where(
        UserModel.provider_issuer == issuer, UserModel.provider_subject == subject,
    ))
    if user is not None:
        return user
    user = UserModel(
        id=uuid4(), provider_issuer=issuer, provider_subject=subject,
        display_name=display_name, email=email, is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def _find_or_create_membership(
    session: Session, *, tenant_id: UUID, user_id: UUID, now: datetime,
) -> TenantMembershipModel:
    membership = session.scalar(select(TenantMembershipModel).where(
        TenantMembershipModel.tenant_id == tenant_id, TenantMembershipModel.user_id == user_id,
    ))
    if membership is not None:
        return membership
    membership = TenantMembershipModel(
        id=uuid4(), tenant_id=tenant_id, user_id=user_id, status=ACTIVE,
        relationship_type='employee', valid_from=now, revision=1,
    )
    session.add(membership)
    session.flush()
    return membership


def _find_or_create_role(session: Session, *, tenant_id: UUID, name: str) -> RoleModel:
    role = session.scalar(select(RoleModel).where(
        RoleModel.tenant_id == tenant_id, RoleModel.name == name,
    ))
    if role is not None:
        return role
    role = RoleModel(id=uuid4(), tenant_id=tenant_id, name=name, is_active=True)
    session.add(role)
    session.flush()
    return role


def _ensure_role_permissions(
    session: Session, *, tenant_id: UUID, role_id: UUID, codes: tuple[str, ...],
) -> None:
    for code in codes:
        permission_id = session.scalar(select(PermissionModel.id).where(
            PermissionModel.code == code, PermissionModel.is_active.is_(True),
        ))
        if permission_id is None:
            raise SystemExit(f'permissão desconhecida no catálogo: {code}')
        exists = session.scalar(select(RolePermissionModel.id).where(
            RolePermissionModel.tenant_id == tenant_id,
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.permission_id == permission_id,
        ))
        if exists is None:
            session.add(RolePermissionModel(
                id=uuid4(), tenant_id=tenant_id, role_id=role_id, permission_id=permission_id,
            ))
    session.flush()


def _ensure_tenant_wide_role_binding(
    session: Session, *, tenant_id: UUID, membership_id: UUID, role_id: UUID, now: datetime,
) -> None:
    exists = session.scalar(select(RoleBindingModel.id).where(
        RoleBindingModel.tenant_id == tenant_id,
        RoleBindingModel.membership_id == membership_id,
        RoleBindingModel.role_id == role_id,
        RoleBindingModel.company_id.is_(None),
        RoleBindingModel.status == ACTIVE,
    ))
    if exists is not None:
        return
    session.add(RoleBindingModel(
        id=uuid4(), tenant_id=tenant_id, membership_id=membership_id, role_id=role_id,
        company_id=None, status=ACTIVE, valid_from=now,
    ))
    session.flush()


def _ensure_company_access(
    session: Session, *, tenant_id: UUID, membership_id: UUID, company_id: UUID, now: datetime,
) -> None:
    exists = session.scalar(select(CompanyAccessModel.id).where(
        CompanyAccessModel.tenant_id == tenant_id,
        CompanyAccessModel.membership_id == membership_id,
        CompanyAccessModel.company_id == company_id,
        CompanyAccessModel.status == ACTIVE,
    ))
    if exists is not None:
        return
    session.add(CompanyAccessModel(
        id=uuid4(), tenant_id=tenant_id, membership_id=membership_id, company_id=company_id,
        status=ACTIVE, valid_from=now,
    ))
    session.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tenant-id', required=True, type=UUID)
    parser.add_argument('--issuer', required=True, help='claim "iss" que o token vai trazer')
    parser.add_argument('--subject', required=True, help='claim "sub"; estável, nunca o e-mail')
    parser.add_argument('--display-name', required=True)
    parser.add_argument('--email', default=None)
    parser.add_argument('--permission', action='append', dest='permissions', default=None)
    args = parser.parse_args()
    permissions = tuple(args.permissions) if args.permissions else DEFAULT_PERMISSIONS

    load_models()
    session = create_session_factory(create_database_engine(AppSettings()))()
    try:
        now = datetime.now(UTC)
        context = AuditContext(
            correlation_id=uuid4(), origin=AuditOrigin.HUMAN,
            reason='Provisionamento de usuário para a ponte de login do Sistema A (ADR 0014)',
        )
        with audit_scope(session, context):
            user = _find_or_create_user(
                session, issuer=args.issuer, subject=args.subject,
                display_name=args.display_name, email=args.email,
            )
            membership = _find_or_create_membership(
                session, tenant_id=args.tenant_id, user_id=user.id, now=now,
            )
            role = _find_or_create_role(session, tenant_id=args.tenant_id, name=DEFAULT_ROLE_NAME)
            _ensure_role_permissions(
                session, tenant_id=args.tenant_id, role_id=role.id, codes=permissions,
            )
            _ensure_tenant_wide_role_binding(
                session, tenant_id=args.tenant_id, membership_id=membership.id,
                role_id=role.id, now=now,
            )
            company_ids = session.scalars(select(CompanyModel.id).where(
                CompanyModel.tenant_id == args.tenant_id, CompanyModel.status == ACTIVE,
            )).all()
            for company_id in company_ids:
                _ensure_company_access(
                    session, tenant_id=args.tenant_id, membership_id=membership.id,
                    company_id=company_id, now=now,
                )
            session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()

    print(json.dumps({
        'event_name': 'user_access.provisioned',
        'user_id': str(user.id),
        'membership_id': str(membership.id),
        'role_id': str(role.id),
        'permissions': list(permissions),
        'companies_granted': len(company_ids),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
