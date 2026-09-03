#!/usr/bin/env python3
"""Catch the silent failures check-package.py does not.

check-package.py guards one failure mode: leakage. This script guards a different one —
a stale vendor fact or a misrouted scope file that produces no error, no missing output,
and no visible symptom, and corrupts a recommendation exactly because nobody notices.

Four checks, all mechanical and deterministic:

    - An expired review date (`Review by YYYY-MM-DD`) anywhere in the package.
    - A price baseline whose re-verification has gone stale past PRICE_STALENESS_DAYS.
    - A scope file in references/opportunities/ that the routing table does not name,
      or a routed filename that does not exist.
    - A relative markdown link that does not resolve to a file on disk.

Kept in its own script and its own CI job on purpose: this is fixable by editing a date
or a table row, never by rotating a credential. That is a different failure mode from
check-package.py's, per CONTRIBUTING.md's "Still open" note on keeping the two separate.

Usage:
    tools/check-consistency.py FILE [FILE ...]
    git ls-files -z '*.md' | xargs -0 tools/check-consistency.py
"""

import re
import sys
from datetime import date
from pathlib import Path

SELF = "tools/check-consistency.py"
TODAY = date.today()

PRICE_STALENESS_DAYS = 90

ROUTING_TABLE = Path("references/opportunity-catalog.md")
OPPORTUNITIES_DIR = Path("references/opportunities")

REVIEW_BY_RX = re.compile(r"Review by (\d{4}-\d{2}-\d{2})")
REVERIFIED_RX = re.compile(r"re-verified against live `list_prices` on (\d{4}-\d{2}-\d{2})")
LINK_RX = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SCHEME_RX = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")  # http:, https:, mailto:, ...
ROUTED_NAME_RX = re.compile(r"opportunities/([\w-]+\.md)")


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_review_dates(path: str, text: str) -> list[str]:
    findings = []
    for m in REVIEW_BY_RX.finditer(text):
        due = date.fromisoformat(m.group(1))
        if due < TODAY:
            findings.append(
                f"{path}:{_line_of(text, m.start())}: review date {due} has passed "
                f"({(TODAY - due).days} days ago) — re-check and move it"
            )
    return findings


def check_price_staleness(path: str, text: str) -> list[str]:
    findings = []
    for m in REVERIFIED_RX.finditer(text):
        verified = date.fromisoformat(m.group(1))
        age = (TODAY - verified).days
        if age > PRICE_STALENESS_DAYS:
            findings.append(
                f"{path}:{_line_of(text, m.start())}: price baseline last verified "
                f"{verified}, {age} days ago (limit {PRICE_STALENESS_DAYS}) — "
                f"re-verify against live list_prices"
            )
    return findings


def check_links(path: str, text: str) -> list[str]:
    findings = []
    base = Path(path).parent
    for m in LINK_RX.finditer(text):
        target = m.group(1).strip()
        if not target or SCHEME_RX.match(target):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue  # pure in-page anchor, e.g. [text](#section)
        target_path = base / target
        if not target_path.exists():
            findings.append(
                f"{path}:{_line_of(text, m.start())}: link target does not resolve: {target}"
            )
    return findings


def check_routing(paths: list[str]) -> list[str]:
    """Whole-repo, not per-file: runs once when the routing table is among the given paths."""
    if str(ROUTING_TABLE) not in paths or not OPPORTUNITIES_DIR.is_dir():
        return []

    table_text = ROUTING_TABLE.read_text(encoding="utf-8")
    routed = set(ROUTED_NAME_RX.findall(table_text))
    existing = {p.name for p in OPPORTUNITIES_DIR.glob("*.md")}

    findings = []
    for name in sorted(existing - routed):
        findings.append(
            f"{OPPORTUNITIES_DIR}/{name}: exists but is not named in {ROUTING_TABLE}'s "
            f"routing table — it will never be considered"
        )
    for name in sorted(routed - existing):
        findings.append(
            f"{ROUTING_TABLE}: routes to opportunities/{name}, which does not exist"
        )
    return findings


def scan(path: str) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return (
        check_review_dates(path, text)
        + check_price_staleness(path, text)
        + check_links(path, text)
    )


def main(argv: list[str]) -> int:
    paths = [p for p in argv if p != SELF and Path(p).is_file()]
    findings = [f for p in paths for f in scan(p)]
    findings += check_routing(paths)

    if not findings:
        print(f"check-consistency: {len(paths)} files, nothing to report")
        return 0

    print("check-consistency: refusing the following\n", file=sys.stderr)
    for f in findings:
        print(f"  {f}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
