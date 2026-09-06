'''Porta de leitura tenant-aware usada pela autorização.'''

from datetime import datetime
from typing import Protocol
from uuid import UUID


class AuthorizationRepository(Protocol):
    def is_user_active(self, user_id: UUID) -> bool: ...

    def find_active_membership(
        self,
        tenant_id: UUID,
        user_id: UUID,
        at: datetime,
    ) -> UUID | None: ...

    def company_belongs_to_tenant(
        self,
        tenant_id: UUID,
        company_id: UUID,
        at: datetime,
    ) -> bool: ...

    def has_active_company_access(
        self,
        tenant_id: UUID,
        membership_id: UUID,
        company_id: UUID,
        at: datetime,
    ) -> bool: ...

    def has_permission(
        self,
        tenant_id: UUID,
        membership_id: UUID,
        company_id: UUID | None,
        permission_code: str,
        at: datetime,
    ) -> bool: ...

    def has_role(
        self, tenant_id: UUID, membership_id: UUID, company_id: UUID | None,
        role_name: str, at: datetime,
    ) -> bool: ...
