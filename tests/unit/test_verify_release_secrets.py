from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify_release_secrets.py"


@pytest.fixture
def scanner():
    spec = importlib.util.spec_from_file_location("verify_release_secrets", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "value",
    [
        b"hunter2",
        b'"abc123"',
        b"'x'",
        b"literal",
        b"None123",
        b"Nonexistent",
        b"$",
        b"${}",
        b"abc$PASSWORD",
    ],
)
def test_detects_literal_and_malformed_password_values(scanner, tmp_path, value) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b"pass" + b"word=" + value)

    assert scanner.findings([candidate]) == [(candidate, "password-assignment", 1)]


def test_detects_prefixed_password_assignments(scanner, tmp_path) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b"MARIADB_ROOT_PASS" + b"WORD=literal")

    assert scanner.findings([candidate]) == [(candidate, "password-assignment", 1)]


@pytest.mark.parametrize(
    "value",
    [
        b"None",
        b"${DB_PASSWORD}",
        b'$DB_PASSWORD',
        b"$(openssl rand -hex 24)",
        b"$env:SERDIAL21_LOCAL_DB_PASSWORD",
        b"'$PASSWORD'",
        b'"${DB_PASSWORD}"',
    ],
)
def test_ignores_only_complete_non_literal_password_values(scanner, tmp_path, value) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b"pass" + b"word = " + value)

    assert scanner.findings([candidate]) == []


def test_ignores_reference_inside_a_larger_quoted_argument(scanner, tmp_path) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b'--env "MARIADB_ROOT_PASS' + b'WORD=${DB_PASSWORD}"')

    assert scanner.findings([candidate]) == []


def test_detects_literal_on_following_line_and_reports_assignment_line(
    scanner, tmp_path
) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b"safe\npass" + b"word =\n  hunter2\n")

    assert scanner.findings([candidate]) == [(candidate, "password-assignment", 2)]


def test_detects_literal_appended_to_quoted_reference(scanner, tmp_path) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b'pass' + b'word="${DB_PASSWORD}"hunter2')

    assert scanner.findings([candidate]) == [(candidate, "password-assignment", 1)]


def test_detects_literal_appended_to_command_substitution(scanner, tmp_path) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b"pass" + b"word=$(generate-secret)hunter2")

    assert scanner.findings([candidate]) == [(candidate, "password-assignment", 1)]


def test_detects_reference_wrapped_in_nested_mixed_quotes(scanner, tmp_path) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b"pass" + b'''word="'$DB_PASSWORD'"''')

    assert scanner.findings([candidate]) == [(candidate, "password-assignment", 1)]


def test_ignores_quoted_reference_followed_by_whitespace(scanner, tmp_path) -> None:
    candidate = tmp_path / "candidate.txt"
    candidate.write_bytes(b'pass' + b'word="${DB_PASSWORD}" trailing-argument')

    assert scanner.findings([candidate]) == []


def test_detects_aws_canary_and_private_key_patterns(scanner, tmp_path) -> None:
    candidate = tmp_path / "candidate.bin"
    candidate.write_bytes(
        b"prefix=" + b"AKIA" + b"0" * 16 + b"\n-----BEGIN RSA " + b"PRIVATE KEY-----\n"
    )

    assert scanner.findings([candidate]) == [
        (candidate, "aws-access-key", 1),
        (candidate, "private-key", 2),
    ]


def test_binary_content_is_scanned_without_text_decoding(scanner, tmp_path) -> None:
    candidate = tmp_path / "candidate.bin"
    candidate.write_bytes(b"\xff\xfepass" + b"word=binary-secret\x00")

    assert scanner.findings([candidate]) == [(candidate, "password-assignment", 1)]


def test_main_reports_path_and_line_without_secret_value(
    scanner, tmp_path, monkeypatch, capsys
) -> None:
    candidate = tmp_path / "nested" / "candidate.txt"
    candidate.parent.mkdir()
    candidate.write_bytes(b"safe\npass" + b"word=do-not-print-this\n")
    monkeypatch.setattr(scanner, "ROOT", tmp_path)

    def candidates() -> list[Path]:
        return [candidate, *tmp_path.glob(".release-secret-canary-*.txt")]

    monkeypatch.setattr(scanner, "candidate_paths", candidates)

    assert scanner.main() == 1
    output = capsys.readouterr().out
    assert (
        "password-assignment: nested\\candidate.txt:2" in output
        or "password-assignment: nested/candidate.txt:2" in output
    )
    assert "do-not-print-this" not in output
