'''Portas para token externo e diretório interno.'''

from typing import Protocol
from uuid import UUID

from serdial21.modules.identity.domain.entities import VerifiedIdentity


class TokenVerifier(Protocol):
    def verify(self, token: str) -> VerifiedIdentity: ...


class IdentityDirectory(Protocol):
    def find_user_id(self, issuer: str, subject: str) -> UUID | None: ...
