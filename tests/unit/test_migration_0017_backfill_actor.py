import importlib.util
from pathlib import Path
from uuid import UUID, uuid4

_PATH = Path(__file__).resolve().parents[2] / 'alembic/versions/20261005_0017_nfe_journey_document_reservations.py'
_SPEC = importlib.util.spec_from_file_location('migration_0017', _PATH)
assert _SPEC and _SPEC.loader
migration = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(migration)


def test_snapshot_actor_converts_json_string_to_uuid() -> None:
    # No snapshot JSON o UUID chega como texto; a coluna Uuid exige UUID (str quebrava o upgrade).
    actor = uuid4()
    assert migration._snapshot_actor({'proposer_id': str(actor)}) == actor
    assert isinstance(migration._snapshot_actor({'proposer_id': str(actor)}), UUID)


def test_snapshot_actor_missing_or_invalid_is_null() -> None:
    assert migration._snapshot_actor({}) is None
    assert migration._snapshot_actor({'proposer_id': 'não-é-uuid'}) is None
    assert migration._snapshot_actor(None) is None
