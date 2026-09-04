'''Porta de autorização exigida antes de qualquer efeito documental.'''

from datetime import datetime
from typing import Protocol
from uuid import UUID


class DocumentAuthorization(Protocol):
    def require_company_manage(
        self,
        tenant_id: UUID,
        company_id: UUID,
        actor_id: UUID | None,
        *,
        at: datetime,
    ) -> None: ...
