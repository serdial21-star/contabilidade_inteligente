'''Consultas SQLAlchemy usadas exclusivamente pela política de autorização.'''

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

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


ACTIVE_STATUS = 'active'


class SqlAlchemyAuthorizationRepository:
    '''Todas as consultas empresariais recebem tenant explicitamente.'''

    def __init__(self, session: Session) -> None:
        self._session = session

    def is_user_active(self, user_id: UUID) -> bool:
        statement = (
            select(UserModel.id)
            .where(
                UserModel.id == user_id,
                UserModel.is_active.is_(True),
            )
            .limit(1)
        )
        return self._session.scalar(statement) is not None

    def find_active_membership(
        self,
        tenant_id: UUID,
        user_id: UUID,
        at: datetime,
    ) -> UUID | None:
        statement = (
            select(TenantMembershipModel.id)
            .where(
                TenantMembershipModel.tenant_id == tenant_id,
                TenantMembershipModel.user_id == user_id,
                TenantMembershipModel.status == ACTIVE_STATUS,
                TenantMembershipModel.valid_from <= at,
                or_(
                    TenantMembershipModel.valid_until.is_(None),
                    TenantMembershipModel.valid_until > at,
                ),
            )
            .order_by(TenantMembershipModel.valid_from.desc())
            .limit(2)
        )
        memberships = list(self._session.scalars(statement))
        if len(memberships) != 1:
            return None
        return memberships[0]

    def company_belongs_to_tenant(
        self,
        tenant_id: UUID,
        company_id: UUID,
        at: datetime,
    ) -> bool:
        statement = (
            select(CompanyModel.id)
            .where(
                CompanyModel.tenant_id == tenant_id,
                CompanyModel.id == company_id,
                CompanyModel.status == ACTIVE_STATUS,
                CompanyModel.valid_from <= at,
                or_(
                    CompanyModel.valid_until.is_(None),
                    CompanyModel.valid_until > at,
                ),
            )
            .limit(1)
        )
        return self._session.scalar(statement) is not None

    def has_active_company_access(
        self,
        tenant_id: UUID,
        membership_id: UUID,
        company_id: UUID,
        at: datetime,
    ) -> bool:
        statement = (
            select(CompanyAccessModel.id)
            .where(
                CompanyAccessModel.tenant_id == tenant_id,
                CompanyAccessModel.membership_id == membership_id,
                CompanyAccessModel.company_id == company_id,
                CompanyAccessModel.status == ACTIVE_STATUS,
                CompanyAccessModel.valid_from <= at,
                or_(
                    CompanyAccessModel.valid_until.is_(None),
                    CompanyAccessModel.valid_until > at,
                ),
            )
            .limit(1)
        )
        return self._session.scalar(statement) is not None

    def has_permission(
        self,
        tenant_id: UUID,
        membership_id: UUID,
        company_id: UUID | None,
        permission_code: str,
        at: datetime,
    ) -> bool:
        scope_condition = (
            RoleBindingModel.company_id.is_(None)
            if company_id is None
            else or_(
                RoleBindingModel.company_id.is_(None),
                RoleBindingModel.company_id == company_id,
            )
        )
        statement = (
            select(RoleBindingModel.id)
            .join(
                RoleModel,
                (RoleModel.tenant_id == RoleBindingModel.tenant_id)
                & (RoleModel.id == RoleBindingModel.role_id),
            )
            .join(
                RolePermissionModel,
                (RolePermissionModel.tenant_id == RoleModel.tenant_id)
                & (RolePermissionModel.role_id == RoleModel.id),
            )
            .join(
                PermissionModel,
                PermissionModel.id == RolePermissionModel.permission_id,
            )
            .where(
                RoleBindingModel.tenant_id == tenant_id,
                RoleBindingModel.membership_id == membership_id,
                RoleBindingModel.status == ACTIVE_STATUS,
                RoleBindingModel.valid_from <= at,
                or_(
                    RoleBindingModel.valid_until.is_(None),
                    RoleBindingModel.valid_until > at,
                ),
                scope_condition,
                RoleModel.tenant_id == tenant_id,
                RoleModel.is_active.is_(True),
                RolePermissionModel.tenant_id == tenant_id,
                PermissionModel.code == permission_code,
                PermissionModel.is_active.is_(True),
            )
            .limit(1)
        )
        return self._session.scalar(statement) is not None

