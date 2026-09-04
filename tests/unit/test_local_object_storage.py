from hashlib import sha256
from pathlib import Path

import pytest

from serdial21.modules.intake_documents.adapters.outbound.storage.local import (
    LocalObjectStorage,
)
from serdial21.modules.intake_documents.application.ports.object_storage import (
    ObjectStorageIntegrityError,
)


def test_stores_and_verifies_content_without_overwriting(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path)
    content = b'conteudo documental imutavel'
    content_hash = sha256(content).hexdigest()
    key = f'tenant/{content_hash[:2]}/{content_hash}'

    first = storage.put_if_absent(key, content, expected_hash=content_hash)
    second = storage.put_if_absent(key, content, expected_hash=content_hash)

    assert first.created is True
    assert second.created is False
    assert storage.read(key) == content
    assert storage.verify(key, expected_hash=content_hash) is True


def test_rejects_hash_mismatch_and_path_traversal(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path)

    with pytest.raises(ObjectStorageIntegrityError):
        storage.put_if_absent('safe/key', b'content', expected_hash='0' * 64)
    with pytest.raises(ValueError):
        storage.put_if_absent(
            '../outside',
            b'content',
            expected_hash=sha256(b'content').hexdigest(),
        )
