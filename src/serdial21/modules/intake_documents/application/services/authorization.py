'''Integração com a fachada pública de autorização do access_control.'''

from datetime import datetime
from uuid import UUID

from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError,
    AuthorizationRequest,
    AuthorizationService,
)
from serdial21.modules.access_control.domain.permissions import PermissionCode


class AccessControlDocumentAuthorization:
    def __init__(self, authorization: AuthorizationService) -> None:
        self._authorization = authorization

    def require_company_manage(
        self,
        tenant_id: UUID,
        company_id: UUID,
        actor_id: UUID | None,
        *,
        at: datetime,
    ) -> None:
        if actor_id is None:
            raise AccessDeniedError()
        self._authorization.require(
            AuthorizationRequest(
                tenant_id=tenant_id,
                user_id=actor_id,
                company_id=company_id,
                permission=PermissionCode('company.manage'),
            ),
            at=at,
        )
