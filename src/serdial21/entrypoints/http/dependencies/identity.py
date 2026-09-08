'''Autenticação Bearer; autorização empresarial permanece na aplicação.'''

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from serdial21.entrypoints.http.dependencies.database import get_db_session
from serdial21.modules.access_control.adapters.outbound.persistence.repositories import (
    SqlAlchemyAuthorizationRepository,
)
from serdial21.modules.access_control.application.services.authorization import AuthorizationService
from serdial21.modules.identity.adapters.inbound.oidc import AuthenticationError
from serdial21.modules.identity.adapters.outbound.persistence.repositories import (
    SqlAlchemyIdentityDirectory,
)
from serdial21.modules.identity.application.ports.authentication import TokenVerifier
from serdial21.modules.identity.application.services.authentication import (
    IdentityContextService,
    IdentityNotLinkedError,
)
from serdial21.modules.identity.domain.entities import AuthenticatedPrincipal


_bearer = HTTPBearer(auto_error=False)


def get_authenticated_principal(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedPrincipal:
    verifier: TokenVerifier | None = request.app.state.oidc_verifier
    if verifier is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='identity unavailable',
        )
    if credentials is None or credentials.scheme.lower() != 'bearer':
        _authentication_failed()
    try:
        identity = verifier.verify(credentials.credentials)
    except AuthenticationError:
        _authentication_failed()
    contexts = IdentityContextService(
        SqlAlchemyIdentityDirectory(session),
        AuthorizationService(SqlAlchemyAuthorizationRepository(session)),
    )
    try:
        return contexts.principal(identity)
    except IdentityNotLinkedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='access denied',
        ) from None


def _authentication_failed() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='authentication failed',
        headers={'WWW-Authenticate': 'Bearer'},
    )
