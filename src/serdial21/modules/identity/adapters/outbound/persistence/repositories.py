'''Lookup mínimo de identidade externa, sem autoridade de tenant.'''

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel,
    CompanyModel,
    RoleBindingModel,
    RoleModel,
    TenantMembershipModel,
    UserModel,
)
from serdial21.modules.identity.application.ports.lifecycle import OffboardingChanges


class SqlAlchemyIdentityDirectory:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_user_id(self, issuer: str, subject: str) -> UUID | None:
        return self._session.scalar(
            select(UserModel.id).where(
                UserModel.provider_issuer == issuer,
                UserModel.provider_subject == subject,
            ).limit(1)
        )


class SqlAlchemyIdentityLifecycleRepository(SqlAlchemyIdentityDirectory):
    def create_user(
        self, issuer: str, subject: str, display_name: str, email: str | None,
    ) -> UUID:
        user_id = uuid4()
        self._session.add(UserModel(
            id=user_id,
            provider_issuer=issuer,
            provider_subject=subject,
            display_name=display_name,
            email=email,
            is_active=True,
        ))
        self._session.flush()
        return user_id

    def activate_user(
        self, user_id: UUID, display_name: str, email: str | None,
    ) -> None:
        user = self._session.get(UserModel, user_id)
        if user is None:
            raise ValueError('usuário interno indisponível')
        user.display_name = display_name
        user.email = email
        user.is_active = True

    def has_active_membership(
        self, tenant_id: UUID, user_id: UUID, at: datetime,
    ) -> bool:
        return self._session.scalar(select(TenantMembershipModel.id).where(
            TenantMembershipModel.tenant_id == tenant_id,
            TenantMembershipModel.user_id == user_id,
            TenantMembershipModel.status == 'active',
            TenantMembershipModel.valid_from <= at,
            or_(
                TenantMembershipModel.valid_until.is_(None),
                TenantMembershipModel.valid_until > at,
            ),
        ).limit(1)) is not None

    def role_is_active(self, tenant_id: UUID, role_id: UUID) -> bool:
        return self._session.scalar(select(RoleModel.id).where(
            RoleModel.tenant_id == tenant_id,
            RoleModel.id == role_id,
            RoleModel.is_active.is_(True),
        ).limit(1)) is not None

    def companies_are_active(
        self, tenant_id: UUID, company_ids: tuple[UUID, ...], at: datetime,
    ) -> bool:
        count = self._session.scalar(select(func.count()).select_from(CompanyModel).where(
            CompanyModel.tenant_id == tenant_id,
            CompanyModel.id.in_(company_ids),
            CompanyModel.status == 'active',
            CompanyModel.valid_from <= at,
            or_(CompanyModel.valid_until.is_(None), CompanyModel.valid_until > at),
        ))
        return count == len(company_ids)

    def create_membership(
        self, tenant_id: UUID, user_id: UUID, relationship_type: str, at: datetime,
    ) -> UUID:
        membership_id = uuid4()
        self._session.add(TenantMembershipModel(
            id=membership_id,
            tenant_id=tenant_id,
            user_id=user_id,
            status='active',
            relationship_type=relationship_type,
            valid_from=at,
            valid_until=None,
            revision=1,
        ))
        # Materializa pais antes das FKs compostas de CompanyAccess/RoleBinding.
        self._session.flush()
        return membership_id

    def grant_company_role(
        self, tenant_id: UUID, membership_id: UUID, company_id: UUID,
        role_id: UUID, at: datetime,
    ) -> None:
        self._session.add_all([
            CompanyAccessModel(
                id=uuid4(), tenant_id=tenant_id, membership_id=membership_id,
                company_id=company_id, status='active', reason='identity onboarding',
                valid_from=at, valid_until=None,
            ),
            RoleBindingModel(
                id=uuid4(), tenant_id=tenant_id, membership_id=membership_id,
                role_id=role_id, company_id=company_id, status='active',
                valid_from=at, valid_until=None,
            ),
        ])

    def offboard(
        self, tenant_id: UUID, user_id: UUID, at: datetime,
    ) -> OffboardingChanges | None:
        memberships = list(self._session.scalars(select(TenantMembershipModel).where(
            TenantMembershipModel.tenant_id == tenant_id,
            TenantMembershipModel.user_id == user_id,
            TenantMembershipModel.status == 'active',
            TenantMembershipModel.valid_from <= at,
            or_(TenantMembershipModel.valid_until.is_(None), TenantMembershipModel.valid_until > at),
        ).limit(2)))
        if len(memberships) != 1:
            return None
        membership = memberships[0]
        accesses = list(self._session.scalars(select(CompanyAccessModel).where(
            CompanyAccessModel.tenant_id == tenant_id,
            CompanyAccessModel.membership_id == membership.id,
            CompanyAccessModel.status == 'active',
        )))
        bindings = list(self._session.scalars(select(RoleBindingModel).where(
            RoleBindingModel.tenant_id == tenant_id,
            RoleBindingModel.membership_id == membership.id,
            RoleBindingModel.status == 'active',
        )))
        membership.status = 'revoked'
        membership.valid_until = at
        membership.revision += 1
        for access in accesses:
            access.status = 'revoked'
            access.valid_until = at
        for binding in bindings:
            binding.status = 'revoked'
            binding.valid_until = at

        other_active = self._session.scalar(select(TenantMembershipModel.id).where(
            TenantMembershipModel.user_id == user_id,
            TenantMembershipModel.id != membership.id,
            TenantMembershipModel.status == 'active',
            TenantMembershipModel.valid_from <= at,
            or_(TenantMembershipModel.valid_until.is_(None), TenantMembershipModel.valid_until > at),
        ).limit(1)) is not None
        user = self._session.get(UserModel, user_id)
        if user is None:
            raise ValueError('usuário interno indisponível')
        user.is_active = other_active
        return OffboardingChanges(
            membership_id=membership.id,
            revoked_company_accesses=len(accesses),
            revoked_role_bindings=len(bindings),
            user_deactivated=not other_active,
        )
