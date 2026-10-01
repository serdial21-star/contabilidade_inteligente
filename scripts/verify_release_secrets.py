"""Fail-closed secret scan for the complete candidate release set."""

from __future__ import annotations

import re
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("private-key", re.compile(rb"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")),
    ("aws-access-key", re.compile(rb"AKIA[0-9A-Z]{16}")),
)
PASSWORD_ASSIGNMENT = re.compile(
    rb"password\s*=\s*(?P<value>"
    rb"\$\([^\r\n]*\)[^\s,;)]*"
    rb"|\"[^\"\r\n]*\"[^\s,;)]*"
    rb"|'[^'\r\n]*'[^\s,;)]*"
    rb"|[^\s,;)]+"
    rb")",
    re.IGNORECASE,
)
SHELL_REFERENCE = re.compile(
    rb"(?:"
    rb"\$[A-Za-z_][A-Za-z0-9_]*"
    rb"|\$\{[A-Za-z_][A-Za-z0-9_]*\}"
    rb"|\$\([^()\r\n]+\)"
    rb"|\$env:[A-Za-z_][A-Za-z0-9_]*"
    rb")",
    re.IGNORECASE,
)

Finding = tuple[Path, str, int]


def candidate_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def _is_non_literal_password(value: bytes) -> bool:
    if value == b"None":
        return True

    unquoted = value
    if len(value) >= 2 and value[:1] == value[-1:] and value[:1] in (b'"', b"'"):
        unquoted = value[1:-1]
    elif value[-1:] in (b'"', b"'"):
        # The opening quote can precede the assignment in a complete CLI argument.
        unquoted = value[:-1]
    return SHELL_REFERENCE.fullmatch(unquoted) is not None


def findings(paths: list[Path]) -> list[Finding]:
    detected: list[Finding] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            content = path.read_bytes()
        except OSError as error:
            raise RuntimeError(f"cannot scan candidate path: {path.relative_to(ROOT)}") from error
        for line_number, line in enumerate(content.splitlines(), start=1):
            for label, pattern in STATIC_PATTERNS:
                if pattern.search(line):
                    detected.append((path, label, line_number))
        for match in PASSWORD_ASSIGNMENT.finditer(content):
            if not _is_non_literal_password(match.group("value")):
                line_number = content.count(b"\n", 0, match.start()) + 1
                detected.append((path, "password-assignment", line_number))
    return detected


def main() -> int:
    canary = ROOT / f".release-secret-canary-{uuid.uuid4().hex}.txt"
    try:
        canary.write_bytes(b"synthetic-canary=" + b"AKIA" + b"0" * 16)
        canary_findings = findings(candidate_paths())
        if not any(
            path == canary and label == "aws-access-key"
            for path, label, _line_number in canary_findings
        ):
            print("SECRET_SCANNER_CANARY_DETECTION: FAIL")
            return 1
    finally:
        canary.unlink(missing_ok=True)

    release_findings = findings(candidate_paths())
    if release_findings:
        print("RELEASE_SECRET_SCAN: FAIL")
        for path, label, line_number in release_findings:
            print(f"{label}: {path.relative_to(ROOT)}:{line_number}")
        return 1

    print("SECRET_SCANNER_CANARY_DETECTION: PASS")
    print("RELEASE_SECRET_SCAN: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
