'''Contrato substituível para armazenamento imutável de objetos.'''

from dataclasses import dataclass
from typing import Protocol


class ObjectStorageIntegrityError(RuntimeError):
    '''Indica conteúdo incompatível com a chave/hash informado.'''


@dataclass(frozen=True, slots=True)
class StoredObject:
    key: str
    size_bytes: int
    content_hash: str
    created: bool


class ObjectStorage(Protocol):
    def put_if_absent(
        self,
        key: str,
        content: bytes,
        *,
        expected_hash: str,
    ) -> StoredObject: ...

    def read(self, key: str) -> bytes: ...

    def verify(self, key: str, *, expected_hash: str) -> bool: ...

