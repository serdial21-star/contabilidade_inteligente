'''Sessão do login único S21 que sobrevive ao F5 (T-0014; mesma decisão do Sistema C, D-059).

A renovação do Supabase fica num cookie HttpOnly, Secure, SameSite=Strict, restrito a estas rotas; nenhum programa da
página o lê. O passe de acesso continua só na memória da tela. Depois da entrega, só o servidor renova (renovação em
paralelo pelo navegador seria vista como reuso e derrubaria a sessão). Só vale para o emissor do login S21; a ponte do
Sistema A continua sem cookie (re-entrada da T-0010).
'''

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from serdial21.bootstrap.settings import AppSettings
from serdial21.entrypoints.http.dependencies.identity import get_authenticated_principal
from serdial21.modules.identity.adapters.inbound.oidc import AuthenticationError
from serdial21.modules.identity.application.ports.authentication import TokenVerifier
from serdial21.modules.identity.application.ports.session import SessionProvider, SessionRefreshError
from serdial21.modules.identity.domain.entities import AuthenticatedPrincipal, VerifiedIdentity
from serdial21.shared_kernel.observability import security_event


router = APIRouter(prefix='/identity/session', tags=['identity'])
COOKIE_NAME = 's21_contabil_session'
# Cabeçalho exigido: formulário ou link de outro site não o envia (defesa além do SameSite=Strict).
SESSION_HEADER = 'X-S21-Session'
_bearer = HTTPBearer(auto_error=False)


class HandoffRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


class SessionResponse(BaseModel):
    access_token: str
    expires_in: int


def _provider(request: Request) -> SessionProvider:
    sessions: SessionProvider | None = request.app.state.s21_sessions
    if sessions is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='session cookie disabled')
    return sessions


def _require_header(value: Annotated[str | None, Header(alias=SESSION_HEADER)] = None) -> None:
    if value != '1':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='access denied')


ProviderDependency = Annotated[SessionProvider, Depends(_provider)]
HeaderGuard = Annotated[None, Depends(_require_header)]
BearerDependency = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _cookie_path(request: Request) -> str:
    settings: AppSettings = request.app.state.settings
    return settings.api_prefix + '/identity/session'


def _verify_s21(request: Request, token: str) -> VerifiedIdentity | None:
    settings: AppSettings = request.app.state.settings
    verifier: TokenVerifier | None = request.app.state.oidc_verifier
    if verifier is None:
        return None
    try:
        identity = verifier.verify(token)
    except AuthenticationError:
        return None
    return identity if identity.issuer == settings.s21_login_issuer else None


def _ended(request: Request) -> JSONResponse:
    response = JSONResponse({'detail': 'session ended'}, status_code=status.HTTP_401_UNAUTHORIZED)
    response.delete_cookie(COOKIE_NAME, path=_cookie_path(request), secure=True, httponly=True, samesite='strict')
    response.headers['Cache-Control'] = 'no-store'
    return response


def _issue(request: Request, refresh_token: str, expected: VerifiedIdentity | None, sessions: SessionProvider,
           event: str) -> JSONResponse:
    '''Renova no Supabase, confere que o passe novo é do login S21, com o código do celular e da mesma pessoa.'''
    try:
        session = sessions.refresh(refresh_token)
    except SessionRefreshError as error:
        if error.kind == 'unavailable':
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail='login service unavailable') from None
        return _ended(request)
    identity = _verify_s21(request, session.access_token)
    same_person = expected is None or (
        identity is not None and (identity.issuer, identity.subject, identity.tenant_id)
        == (expected.issuer, expected.subject, expected.tenant_id))
    if identity is None or not same_person:
        sessions.logout(session.access_token)
        security_event('session.denied', fields={'reason': 'identity_mismatch' if identity else 'token_rejected'})
        return _ended(request)
    security_event(event, fields={'subject': identity.subject})
    settings: AppSettings = request.app.state.settings
    response = JSONResponse({'access_token': session.access_token, 'expires_in': session.expires_in})
    response.set_cookie(COOKIE_NAME, session.refresh_token, max_age=settings.s21_session_cookie_max_age_seconds,
                        path=_cookie_path(request), secure=True, httponly=True, samesite='strict')
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('', response_model=SessionResponse)
def handoff(
    body: HandoffRequest,
    request: Request,
    _: Annotated[AuthenticatedPrincipal, Depends(get_authenticated_principal)],
    credentials: BearerDependency,
    sessions: ProviderDependency,
    __: HeaderGuard,
) -> JSONResponse:
    '''Depois do código do celular, a tela entrega a renovação; o servidor renova uma vez e a guarda no cookie.'''
    assert credentials is not None  # get_authenticated_principal já recusou a falta de passe
    expected = _verify_s21(request, credentials.credentials)
    if expected is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='access denied')
    return _issue(request, body.refresh_token, expected, sessions, 'session.started')


@router.post('/refresh', response_model=SessionResponse)
def refresh(request: Request, sessions: ProviderDependency, _: HeaderGuard) -> JSONResponse:
    '''Passe novo a partir do cookie (F5, recarga ou passe perto de vencer). Sem cookie válido: 401 e cookie apagado.'''
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return _ended(request)
    return _issue(request, token, None, sessions, 'session.refreshed')


@router.post('/logout')
def logout(request: Request, credentials: BearerDependency, _: HeaderGuard) -> JSONResponse:
    '''Sair: encerra no Supabase (melhor esforço) e apaga o cookie, mesmo sem passe válido.'''
    sessions: SessionProvider | None = request.app.state.s21_sessions
    if (credentials is not None and credentials.scheme.lower() == 'bearer' and sessions is not None
            and _verify_s21(request, credentials.credentials) is not None):
        sessions.logout(credentials.credentials)
        security_event('session.ended')
    response = JSONResponse({'signed_out': True})
    response.delete_cookie(COOKIE_NAME, path=_cookie_path(request), secure=True, httponly=True, samesite='strict')
    response.headers['Cache-Control'] = 'no-store'
    return response
