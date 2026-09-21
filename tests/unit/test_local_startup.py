"""Regressões de segurança do inicializador local."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "start_local.py"
SPEC = spec_from_file_location("start_local", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
START_LOCAL = module_from_spec(SPEC)
SPEC.loader.exec_module(START_LOCAL)


def test_public_interface_paths_are_allowed() -> None:
    assert START_LOCAL.is_public_path("/app/")
    assert START_LOCAL.is_public_path("/app/index.html?cache=off")
    assert START_LOCAL.is_public_path("/ui/assets/brand/logo.png")


def test_repository_and_traversal_paths_are_blocked() -> None:
    assert not START_LOCAL.is_public_path("/.env")
    assert not START_LOCAL.is_public_path("/src/serdial21/main.py")
    assert not START_LOCAL.is_public_path("/app/../.env")
    assert not START_LOCAL.is_public_path("/app/%2e%2e/.git/config")
