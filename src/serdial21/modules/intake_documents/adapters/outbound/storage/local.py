'''ObjectStorage local e imutável para desenvolvimento e testes.'''

from hashlib import sha256
import os
from pathlib import Path

from serdial21.modules.intake_documents.application.ports.object_storage import (
    ObjectStorageIntegrityError,
    StoredObject,
)


class LocalObjectStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def put_if_absent(
        self,
        key: str,
        content: bytes,
        *,
        expected_hash: str,
    ) -> StoredObject:
        actual_hash = sha256(content).hexdigest()
        if actual_hash != expected_hash:
            raise ObjectStorageIntegrityError('hash do conteúdo não confere')
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            with target.open('xb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            created = True
        except FileExistsError:
            if not self.verify(key, expected_hash=expected_hash):
                raise ObjectStorageIntegrityError(
                    'objeto existente possui conteúdo incompatível'
                )
        return StoredObject(
            key=key,
            size_bytes=len(content),
            content_hash=actual_hash,
            created=created,
        )

    def read(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def verify(self, key: str, *, expected_hash: str) -> bool:
        target = self._resolve(key)
        if not target.is_file():
            return False
        return sha256(target.read_bytes()).hexdigest() == expected_hash

    def _resolve(self, key: str) -> Path:
        if not key or Path(key).is_absolute():
            raise ValueError('chave de storage deve ser relativa')
        target = (self._root / Path(key)).resolve()
        if not target.is_relative_to(self._root):
            raise ValueError('chave de storage fora do diretório permitido')
        return target
