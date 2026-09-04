from datetime import UTC, datetime
from uuid import uuid4

import pytest

from serdial21.modules.access_control.application.services.authorization import (
    AccessDeniedError,
    AuthorizationRequest,
)
from serdial21.modules.intake_documents.application.services.authorization import (
    AccessControlDocumentAuthorization,
)


class RecordingAuthorizationService:
    def __init__(self) -> None:
        self.request: AuthorizationRequest | None = None
        self.at: datetime | None = None

    def require(self, request: AuthorizationRequest, *, at: datetime) -> object:
        self.request = request
        self.at = at
        return object()


def test_document_authorization_requires_company_manage() -> None:
    tenant_id, company_id, actor_id = uuid4(), uuid4(), uuid4()
    checked_at = datetime(2026, 9, 4, 15, 0, tzinfo=UTC)
    authorization = RecordingAuthorizationService()
    guard = AccessControlDocumentAuthorization(authorization)  # type: ignore[arg-type]

    guard.require_company_manage(
        tenant_id,
        company_id,
        actor_id,
        at=checked_at,
    )

    assert authorization.request is not None
    assert authorization.request.tenant_id == tenant_id
    assert authorization.request.company_id == company_id
    assert authorization.request.user_id == actor_id
    assert authorization.request.permission.value == 'company.manage'
    assert authorization.at == checked_at


def test_document_authorization_rejects_missing_actor() -> None:
    guard = AccessControlDocumentAuthorization(
        RecordingAuthorizationService(),  # type: ignore[arg-type]
    )

    with pytest.raises(AccessDeniedError):
        guard.require_company_manage(uuid4(), uuid4(), None, at=datetime.now(UTC))
