'''Porta da sessão que sobrevive ao F5 (T-0014; mesma decisão do Sistema C, D-059).'''

from dataclasses import dataclass
from typing import Protocol


class SessionRefreshError(Exception):
    '''invalid = renovação recusada (a sessão terminou); unavailable = serviço de login sem resposta.'''

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


@dataclass(frozen=True)
class RefreshedSession:
    access_token: str
    refresh_token: str
    expires_in: int

    def __repr__(self) -> str:
        return f'RefreshedSession(expires_in={self.expires_in})'


class SessionProvider(Protocol):
    def refresh(self, refresh_token: str) -> RefreshedSession: ...

    def logout(self, access_token: str) -> None: ...
