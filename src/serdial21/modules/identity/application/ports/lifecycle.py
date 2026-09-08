'''Porta de persistência para onboarding e offboarding.'''

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OffboardingChanges:
    membership_id: UUID
    revoked_company_accesses: int
    revoked_role_bindings: int
    user_deactivated: bool


class IdentityLifecycleRepository(Protocol):
    def find_user_id(self, issuer: str, subject: str) -> UUID | None: ...
    def create_user(
        self, issuer: str, subject: str, display_name: str, email: str | None,
    ) -> UUID: ...
    def activate_user(
        self, user_id: UUID, display_name: str, email: str | None,
    ) -> None: ...
    def has_active_membership(self, tenant_id: UUID, user_id: UUID, at: datetime) -> bool: ...
    def role_is_active(self, tenant_id: UUID, role_id: UUID) -> bool: ...
    def companies_are_active(
        self, tenant_id: UUID, company_ids: tuple[UUID, ...], at: datetime,
    ) -> bool: ...
    def create_membership(
        self, tenant_id: UUID, user_id: UUID, relationship_type: str, at: datetime,
    ) -> UUID: ...
    def grant_company_role(
        self, tenant_id: UUID, membership_id: UUID, company_id: UUID,
        role_id: UUID, at: datetime,
    ) -> None: ...
    def offboard(
        self, tenant_id: UUID, user_id: UUID, at: datetime,
    ) -> OffboardingChanges | None: ...
