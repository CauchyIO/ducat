"""Tests for tools/check-consistency.py, the checker for silent staleness in the package."""

from pathlib import Path

import pytest


def test_expired_review_date_is_flagged(check_consistency, today):
    """A review date before today is flagged; today itself and future dates are not."""
    text = "Review by 2026-09-03\nReview by 2026-09-04\nReview by 2027-01-01\n"
    findings = check_consistency.check_review_dates("f.md", text)
    assert len(findings) == 1
    assert findings[0].startswith("f.md:1:")


def test_findings_carry_the_right_line_number(check_consistency, today):
    """A finding below the first line reports the line it is actually on."""
    text = "fine\n\nstill fine\nReview by 2020-01-01\n"
    findings = check_consistency.check_review_dates("f.md", text)
    assert len(findings) == 1
    assert findings[0].startswith("f.md:4: review date 2020-01-01 has passed")


@pytest.mark.parametrize(
    ("verified", "flagged"),
    [
        ("2026-06-06", False),  # exactly 90 days
        ("2026-06-05", True),  # 91 days
    ],
)
def test_price_staleness_limit(check_consistency, today, verified, flagged):
    """A price baseline is stale on day 91 and not on day 90."""
    text = f"re-verified against live `list_prices` on {verified}\n"
    findings = check_consistency.check_price_staleness("f.md", text)
    assert bool(findings) is flagged


def test_links_resolve_relative_to_the_file(check_consistency, tmp_path: Path):
    """Only a relative link to a file that does not exist is flagged.

    Links with a URL scheme, pure in-page anchors and empty targets are skipped, and a
    link with a fragment is checked by its file part alone.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "b.md").write_text("")
    text = (
        "[ok](b.md) [frag](b.md#section) [anchor](#top) [web](https://x.example)"
        " [mail](mailto:a@b.c) [empty]() [missing](c.md)\n"
    )
    findings = check_consistency.check_links(str(docs / "a.md"), text)
    assert len(findings) == 1
    assert findings[0].endswith("link target does not resolve: c.md")


def test_routing_in_both_directions(check_consistency, tmp_path: Path, monkeypatch):
    """A scope file the table does not name, and a table entry with no file, are both flagged.

    The check only runs when the routing table itself is among the files being scanned.
    """
    monkeypatch.chdir(tmp_path)
    opps = tmp_path / "references" / "opportunities"
    opps.mkdir(parents=True)
    (opps / "job.md").write_text("")
    (opps / "orphan.md").write_text("")
    table = tmp_path / "references" / "opportunity-catalog.md"
    table.write_text("| job | opportunities/job.md |\n| ghost | opportunities/ghost.md |\n")

    findings = check_consistency.check_routing(["references/opportunity-catalog.md"])
    assert len(findings) == 2
    assert "orphan.md" in findings[0] and "not named" in findings[0]
    assert "ghost.md" in findings[1] and "does not exist" in findings[1]

    assert check_consistency.check_routing(["docs/other.md"]) == []


def test_routing_needs_the_opportunities_directory(check_consistency, tmp_path: Path, monkeypatch):
    """With no opportunities directory there is nothing to route, so nothing is flagged."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "opportunity-catalog.md").write_text("opportunities/ghost.md\n")
    assert check_consistency.check_routing(["references/opportunity-catalog.md"]) == []


def test_main_exit_codes(check_consistency, today, tmp_path: Path, monkeypatch, capsys):
    """Exit 0 when every file is current, 1 with the finding on stderr when one is not."""
    monkeypatch.chdir(tmp_path)
    clean = tmp_path / "clean.md"
    clean.write_text("Review by 2027-01-01\n")
    stale = tmp_path / "stale.md"
    stale.write_text("Review by 2020-01-01\n")
    assert check_consistency.main([str(clean)]) == 0
    assert check_consistency.main([str(clean), str(stale)]) == 1
    assert "review date 2020-01-01 has passed" in capsys.readouterr().err
