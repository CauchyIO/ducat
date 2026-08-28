#!/usr/bin/env python3
"""Refuse credentials and one estate's identifiers before they leave the machine.

Two rule groups, deliberately different in scope.

Credentials are refused in every file passed. Estate identifiers are refused only in
the package a client reads: SKILL.md, references/, docs/, and the configuration beside
them. A workspace id in a gitignored working note is nobody's problem; the same id in a
runbook is what a client sees.

Identifiers are matched by shape, never by value. A checker holding a list of the ids it
forbids would be the leak it exists to prevent, and it would only ever protect one estate.

Usage:
    tools/check-package.py FILE [FILE ...]
    git ls-files -z | xargs -0 tools/check-package.py

A line containing `check-allow` is skipped. Use it for a deliberate example, and say in
the surrounding prose why the example is safe.
"""

import re
import sys
from pathlib import Path

SELF = "tools/check-package.py"

PACKAGE_ROOTS = ("SKILL.md", "README.md", "NOTICE.md", ".mcp.json",
                 "references/", "docs/", ".claude/")

CREDENTIALS = [
    ("databricks-token", r"\bdapi[0-9a-f]{32}\b"),
    ("databricks-oauth-secret", r"\bdose[0-9a-f]{32}\b"),
    ("private-key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("json-web-token", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("assigned-secret",
     r"(?i)\b(client[_-]?secret|password|api[_-]?key|access[_-]?token)\b\s*[:=]\s*"
     r"[\"']?[A-Za-z0-9+/_.~-]{20,}"),
]

IDENTIFIERS = [
    ("workspace-hostname", r"\badb-\d{8,}\.\d+\.azuredatabricks\.net\b"),
    ("workspace-id", r"\b\d{15,16}\b"),
    ("guid", r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    ("warehouse-id", r"\b[0-9a-f]{16}\b"),
]

CRED_RX = [(n, re.compile(p)) for n, p in CREDENTIALS]
IDENT_RX = [(n, re.compile(p)) for n, p in IDENTIFIERS]


def in_package(path: str) -> bool:
    return any(path == r or path.startswith(r) for r in PACKAGE_ROOTS)


def scan(path: str) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    rules = list(CRED_RX)
    if in_package(path):
        rules += IDENT_RX

    findings = []
    for n, line in enumerate(text.splitlines(), 1):
        if "check-allow" in line:
            continue
        for name, rx in rules:
            m = rx.search(line)
            if m:
                findings.append(f"{path}:{n}: {name}: {m.group(0)[:40]}")
    return findings


def main(argv: list[str]) -> int:
    paths = [p for p in argv if p != SELF and Path(p).is_file()]
    findings = [f for p in paths for f in scan(p)]

    if not findings:
        print(f"check-package: {len(paths)} files, nothing to report")
        return 0

    print("check-package: refusing the following\n", file=sys.stderr)
    for f in findings:
        print(f"  {f}", file=sys.stderr)
    print(
        "\nA credential must be rotated, not merely deleted — it is already on this machine\n"
        "and may be in the history. An estate identifier belongs in environment.local.md,\n"
        "with a placeholder such as <workspace-id> in its place.\n"
        "A deliberate example needs `check-allow` on the line and a reason in the prose.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
