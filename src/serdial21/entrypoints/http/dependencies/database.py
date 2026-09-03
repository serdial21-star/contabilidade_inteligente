'''Sessão transacional por requisição.'''

from collections.abc import Generator

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from serdial21.bootstrap.database import DatabaseRuntime, session_scope


def get_db_session(request: Request) -> Generator[Session, None, None]:
    runtime: DatabaseRuntime = request.app.state.database
    if runtime.session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='database unavailable',
        )

    with session_scope(runtime.session_factory) as session:
        yield session
