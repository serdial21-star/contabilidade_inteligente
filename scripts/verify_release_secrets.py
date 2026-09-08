"""Fail-closed secret scan for the complete candidate release set."""

from __future__ import annotations

import re
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("private-key", re.compile(rb"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")),
    ("aws-access-key", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("password-assignment", re.compile(rb"password\s*=\s*[^\s]+", re.IGNORECASE)),
)


def candidate_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def findings(paths: list[Path]) -> list[tuple[Path, str]]:
    detected: list[tuple[Path, str]] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            content = path.read_bytes()
        except OSError as error:
            raise RuntimeError(f"cannot scan candidate path: {path.relative_to(ROOT)}") from error
        for label, pattern in PATTERNS:
            if pattern.search(content):
                detected.append((path, label))
    return detected


def main() -> int:
    canary = ROOT / f".release-secret-canary-{uuid.uuid4().hex}.txt"
    try:
        canary.write_bytes(b"synthetic-canary=" + b"AKIA" + b"0" * 16)
        canary_findings = findings(candidate_paths())
        if not any(path == canary and label == "aws-access-key" for path, label in canary_findings):
            print("SECRET_SCANNER_CANARY_DETECTION: FAIL")
            return 1
    finally:
        canary.unlink(missing_ok=True)

    release_findings = findings(candidate_paths())
    if release_findings:
        print("RELEASE_SECRET_SCAN: FAIL")
        for path, label in release_findings:
            print(f"{label}: {path.relative_to(ROOT)}")
        return 1

    print("SECRET_SCANNER_CANARY_DETECTION: PASS")
    print("RELEASE_SECRET_SCAN: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
