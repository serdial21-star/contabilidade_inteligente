'''Entidades puras da fronteira de acesso.'''

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from serdial21.modules.access_control.domain.permissions import PermissionCode


@dataclass(frozen=True, slots=True)
class Tenant:
    id: UUID
    name: str
    timezone: str
    currency_code: str
    status: str


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    provider_subject: str
    display_name: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class TenantMembership:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    status: str
    valid_from: datetime
    valid_until: datetime | None
    revision: int


@dataclass(frozen=True, slots=True)
class Company:
    id: UUID
    tenant_id: UUID
    legal_name: str
    tax_identifier: str
    status: str


@dataclass(frozen=True, slots=True)
class Establishment:
    id: UUID
    tenant_id: UUID
    company_id: UUID
    name: str
    tax_identifier: str
    status: str


@dataclass(frozen=True, slots=True)
class CompanyAccess:
    id: UUID
    tenant_id: UUID
    membership_id: UUID
    company_id: UUID
    status: str
    valid_from: datetime
    valid_until: datetime | None


@dataclass(frozen=True, slots=True)
class Role:
    id: UUID
    tenant_id: UUID
    name: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class Permission:
    id: UUID
    code: PermissionCode
    description: str
    version: int
    is_active: bool


@dataclass(frozen=True, slots=True)
class RolePermission:
    id: UUID
    tenant_id: UUID
    role_id: UUID
    permission_id: UUID


@dataclass(frozen=True, slots=True)
class RoleBinding:
    id: UUID
    tenant_id: UUID
    membership_id: UUID
    role_id: UUID
    company_id: UUID | None
    status: str
    valid_from: datetime
    valid_until: datetime | None

