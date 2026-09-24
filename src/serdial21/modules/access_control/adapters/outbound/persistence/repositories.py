'''Consultas SQLAlchemy usadas exclusivamente pela política de autorização.'''

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from serdial21.modules.access_control.adapters.outbound.persistence.models import (
    CompanyAccessModel,
    CompanyModel,
    CompanyTeamAssignmentModel,
    OfficeTeamMemberModel,
    PermissionModel,
    RoleBindingModel,
    RoleModel,
    RolePermissionModel,
    TenantMembershipModel,
    UserModel,
)
from serdial21.modules.access_control.application.services.company_import import (
    CompanySnapshot,
    IMPORT_DEFAULT_CURRENCY_CODE,
    IMPORT_DEFAULT_TIMEZONE,
    MappedCompany,
)
from serdial21.modules.access_control.application.services.team_import import (
    MappedTeamMember,
    TeamMemberSnapshot,
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


    def has_role(
        self, tenant_id: UUID, membership_id: UUID, company_id: UUID | None,
        role_name: str, at: datetime,
    ) -> bool:
        scope = RoleBindingModel.company_id.is_(None)
        if company_id is not None:
            scope = or_(scope, RoleBindingModel.company_id == company_id)
        return self._session.scalar(
            select(RoleBindingModel.id).join(RoleModel,
                (RoleModel.tenant_id == RoleBindingModel.tenant_id)
                & (RoleModel.id == RoleBindingModel.role_id),
            ).where(
                RoleBindingModel.tenant_id == tenant_id,
                RoleBindingModel.membership_id == membership_id,
                RoleBindingModel.status == ACTIVE_STATUS,
                RoleBindingModel.valid_from <= at,
                or_(RoleBindingModel.valid_until.is_(None), RoleBindingModel.valid_until > at),
                scope, RoleModel.name == role_name, RoleModel.is_active.is_(True),
            ).limit(1)
        ) is not None

    def list_active_companies(
        self, tenant_id: UUID, membership_id: UUID, at: datetime,
    ) -> tuple[tuple[UUID, str], ...]:
        statement = (
            select(CompanyModel.id, CompanyModel.trade_name, CompanyModel.legal_name)
            .distinct()
            .join(
                CompanyAccessModel,
                (CompanyAccessModel.tenant_id == CompanyModel.tenant_id)
                & (CompanyAccessModel.company_id == CompanyModel.id),
            )
            .where(
                CompanyModel.tenant_id == tenant_id,
                CompanyModel.status == ACTIVE_STATUS,
                CompanyModel.valid_from <= at,
                or_(CompanyModel.valid_until.is_(None), CompanyModel.valid_until > at),
                CompanyAccessModel.tenant_id == tenant_id,
                CompanyAccessModel.membership_id == membership_id,
                CompanyAccessModel.status == ACTIVE_STATUS,
                CompanyAccessModel.valid_from <= at,
                or_(
                    CompanyAccessModel.valid_until.is_(None),
                    CompanyAccessModel.valid_until > at,
                ),
            )
            .order_by(CompanyModel.legal_name, CompanyModel.id)
        )
        return tuple(
            (company_id, trade_name or legal_name)
            for company_id, trade_name, legal_name in self._session.execute(statement)
        )

    def list_permissions(
        self, tenant_id: UUID, membership_id: UUID,
        company_id: UUID | None, at: datetime,
    ) -> tuple[str, ...]:
        scope = RoleBindingModel.company_id.is_(None)
        if company_id is not None:
            scope = or_(scope, RoleBindingModel.company_id == company_id)
        statement = (
            select(PermissionModel.code)
            .select_from(RoleBindingModel)
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
            .join(PermissionModel, PermissionModel.id == RolePermissionModel.permission_id)
            .where(
                RoleBindingModel.tenant_id == tenant_id,
                RoleBindingModel.membership_id == membership_id,
                RoleBindingModel.status == ACTIVE_STATUS,
                RoleBindingModel.valid_from <= at,
                or_(RoleBindingModel.valid_until.is_(None), RoleBindingModel.valid_until > at),
                scope,
                RoleModel.tenant_id == tenant_id,
                RoleModel.is_active.is_(True),
                RolePermissionModel.tenant_id == tenant_id,
                PermissionModel.is_active.is_(True),
            )
            .distinct()
            .order_by(PermissionModel.code)
        )
        return tuple(self._session.scalars(statement))


class SqlAlchemyCompanyImportRepository:
    '''Leitura e gravação estreitas usadas somente pelo import manual (ADR 0013).'''

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_external_reference(
        self, tenant_id: UUID, external_system: str, external_type: str, external_id: str,
    ) -> CompanySnapshot | None:
        statement = select(CompanyModel).where(
            CompanyModel.tenant_id == tenant_id,
            CompanyModel.external_system == external_system,
            CompanyModel.external_type == external_type,
            CompanyModel.external_id == external_id,
        ).limit(1)
        model = self._session.scalar(statement)
        return _to_snapshot(model) if model is not None else None

    def find_by_tax_identifier(
        self, tenant_id: UUID, tax_identifier: str,
    ) -> CompanySnapshot | None:
        statement = select(CompanyModel).where(
            CompanyModel.tenant_id == tenant_id,
            CompanyModel.tax_identifier == tax_identifier,
        ).limit(1)
        model = self._session.scalar(statement)
        return _to_snapshot(model) if model is not None else None

    def create(
        self, tenant_id: UUID, mapped: MappedCompany, *, external_system: str, now: datetime,
    ) -> UUID:
        model = CompanyModel(
            id=uuid4(),
            tenant_id=tenant_id,
            legal_name=mapped.legal_name,
            trade_name=mapped.trade_name,
            tax_identifier=mapped.tax_identifier,
            timezone=IMPORT_DEFAULT_TIMEZONE,
            currency_code=IMPORT_DEFAULT_CURRENCY_CODE,
            status=mapped.status,
            external_system=external_system,
            external_type=mapped.external_type,
            external_id=mapped.external_id,
            valid_from=now,
        )
        self._session.add(model)
        self._session.flush()
        return model.id


class SqlAlchemyTeamImportRepository:
    '''Leitura e gravação estreitas da equipe interna, sempre escopadas por tenant.'''

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_member_by_external_reference(
        self, tenant_id: UUID, external_system: str, external_type: str, external_id: str,
    ) -> TeamMemberSnapshot | None:
        model = self._session.scalar(select(OfficeTeamMemberModel).where(
            OfficeTeamMemberModel.tenant_id == tenant_id,
            OfficeTeamMemberModel.external_system == external_system,
            OfficeTeamMemberModel.external_type == external_type,
            OfficeTeamMemberModel.external_id == external_id,
        ).limit(1))
        return _to_member_snapshot(model) if model is not None else None

    def find_member_by_email(self, tenant_id: UUID, email: str) -> TeamMemberSnapshot | None:
        model = self._session.scalar(select(OfficeTeamMemberModel).where(
            OfficeTeamMemberModel.tenant_id == tenant_id,
            OfficeTeamMemberModel.email == email,
        ).limit(1))
        return _to_member_snapshot(model) if model is not None else None

    def list_members(self, tenant_id: UUID) -> list[TeamMemberSnapshot]:
        return [
            _to_member_snapshot(model)
            for model in self._session.scalars(select(OfficeTeamMemberModel).where(
                OfficeTeamMemberModel.tenant_id == tenant_id,
            ).order_by(OfficeTeamMemberModel.display_name, OfficeTeamMemberModel.id))
        ]

    def create_member(
        self, tenant_id: UUID, mapped: MappedTeamMember, *, external_system: str,
        external_type: str, now: datetime,
    ) -> UUID:
        model = OfficeTeamMemberModel(
            id=uuid4(), tenant_id=tenant_id, display_name=mapped.display_name,
            email=mapped.email, job_title=mapped.job_title, status=mapped.status,
            external_system=external_system, external_type=external_type,
            external_id=mapped.external_id, valid_from=now,
        )
        self._session.add(model)
        self._session.flush()
        return model.id

    def find_company_id_by_external_reference(
        self, tenant_id: UUID, external_system: str, external_type: str, external_id: str,
    ) -> UUID | None:
        return self._session.scalar(select(CompanyModel.id).where(
            CompanyModel.tenant_id == tenant_id,
            CompanyModel.external_system == external_system,
            CompanyModel.external_type == external_type,
            CompanyModel.external_id == external_id,
        ).limit(1))

    def assignment_exists(
        self, tenant_id: UUID, company_id: UUID, member_id: UUID, role_label: str,
    ) -> bool:
        return self._session.scalar(select(CompanyTeamAssignmentModel.id).where(
            CompanyTeamAssignmentModel.tenant_id == tenant_id,
            CompanyTeamAssignmentModel.company_id == company_id,
            CompanyTeamAssignmentModel.team_member_id == member_id,
            CompanyTeamAssignmentModel.role_label == role_label,
        ).limit(1)) is not None

    def create_assignment(
        self, tenant_id: UUID, company_id: UUID, member_id: UUID, role_label: str,
        *, now: datetime,
    ) -> UUID:
        model = CompanyTeamAssignmentModel(
            id=uuid4(), tenant_id=tenant_id, company_id=company_id,
            team_member_id=member_id, role_label=role_label, status='active', valid_from=now,
        )
        self._session.add(model)
        self._session.flush()
        return model.id


def _to_member_snapshot(model: OfficeTeamMemberModel) -> TeamMemberSnapshot:
    return TeamMemberSnapshot(
        id=model.id, display_name=model.display_name, email=model.email,
        job_title=model.job_title, status=model.status, external_id=model.external_id,
    )


def _to_snapshot(model: CompanyModel) -> CompanySnapshot:
    return CompanySnapshot(
        id=model.id,
        legal_name=model.legal_name,
        trade_name=model.trade_name,
        tax_identifier=model.tax_identifier,
        status=model.status,
        external_id=model.external_id,
    )
