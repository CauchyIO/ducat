"""Tests for tools/check-consistency.py, the checker for silent staleness in the package."""

from datetime import date, timedelta
from pathlib import Path
from types import ModuleType

import pytest


def test_expired_review_date_is_flagged(check_consistency, today):
    """A review date before today is flagged; today itself and future dates are not.

    Dates are offsets from the pinned `today`, never literals, so the test means the same
    thing whatever the pinned date is.
    """
    yesterday, tomorrow = today - timedelta(days=1), today + timedelta(days=1)
    text = f"Review by {yesterday}\nReview by {today}\nReview by {tomorrow}\n"
    findings = check_consistency.check_review_dates("f.md", text)
    assert len(findings) == 1
    assert findings[0].startswith(f"f.md:1: review date {yesterday} has passed")


def test_findings_carry_the_right_line_number(check_consistency, today):
    """A finding below the first line reports the line it is actually on."""
    expired = today - timedelta(days=1)
    text = f"fine\n\nstill fine\nReview by {expired}\n"
    findings = check_consistency.check_review_dates("f.md", text)
    assert len(findings) == 1
    assert findings[0].startswith(f"f.md:4: review date {expired} has passed")


@pytest.mark.parametrize(("days_ago", "flagged"), [(90, False), (91, True)])
def test_price_staleness_limit(check_consistency, today, days_ago, flagged):
    """A price baseline is stale on day 91 and not on day 90."""
    verified = today - timedelta(days=days_ago)
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


def _write_required_files(root: Path, review: str, reverified: str) -> None:
    """Writes the two files `REQUIRED_MARKERS` names, carrying the given sentences.

    Args:
        root: Directory to write the `references/` tree under.
        review: Full contents of `references/freshness.md`.
        reverified: Full contents of `references/opportunity-catalog.md`.
    """
    references = root / "references"
    references.mkdir(parents=True, exist_ok=True)
    (references / "freshness.md").write_text(review)
    (references / "opportunity-catalog.md").write_text(reverified)


def test_required_markers_are_silent_when_both_are_present(
    check_consistency: ModuleType, today: date, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both sentences intact is the ordinary case and produces nothing."""
    monkeypatch.chdir(tmp_path)
    _write_required_files(
        tmp_path,
        review=f"# Freshness\n\n**Distilled {today}. Review by {today}.**\n",
        reverified=f"**As of {today}, re-verified against live `list_prices` on {today}.**\n",
    )
    assert check_consistency.check_required_markers() == []


def test_rewording_the_review_sentence_is_a_finding(
    check_consistency: ModuleType, today: date, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A freshness file whose review phrase was reworded away is flagged, not passed.

    This is the case no other test can reach: `check_review_dates` sees no date, so it
    has nothing to report, and the run would otherwise be green.
    """
    monkeypatch.chdir(tmp_path)
    _write_required_files(
        tmp_path,
        review=f"# Freshness\n\nPlease revisit this by {today}.\n",
        reverified=f"**As of {today}, re-verified against live `list_prices` on {today}.**\n",
    )
    findings = check_consistency.check_required_markers()
    assert len(findings) == 1
    assert findings[0].startswith('references/freshness.md: carries no "Review by')


def test_rewording_the_reverification_sentence_is_a_finding(
    check_consistency: ModuleType, today: date, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A price baseline whose re-verification phrase was reworded away is flagged."""
    monkeypatch.chdir(tmp_path)
    _write_required_files(
        tmp_path,
        review=f"# Freshness\n\n**Review by {today}.**\n",
        reverified=f"**As of {today}, checked against list_prices on {today}.**\n",
    )
    findings = check_consistency.check_required_markers()
    assert len(findings) == 1
    assert findings[0].startswith('references/opportunity-catalog.md: carries no "re-verified')


def test_required_markers_flag_a_file_that_is_gone(
    check_consistency: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A renamed or deleted reference is a finding, which is why the check is unconditional.

    Anchoring on the scanned paths, the way `check_routing` does, could never catch this:
    a file that no longer exists is never among them.
    """
    monkeypatch.chdir(tmp_path)
    findings = check_consistency.check_required_markers()
    assert len(findings) == 2
    assert all("cannot be read" in f for f in findings)


def test_main_exit_codes(check_consistency, today, tmp_path: Path, monkeypatch, capsys):
    """Exit 0 when every file is current, 1 with the finding on stderr when one is not."""
    monkeypatch.chdir(tmp_path)
    # This test is about what a per-file finding does to the exit code. The required-file
    # check runs on every invocation and would fail from a directory that has no
    # references/ tree, which is every tmp_path; its own tests cover it above.
    monkeypatch.setattr(check_consistency, "REQUIRED_MARKERS", {})
    clean = tmp_path / "clean.md"
    clean.write_text(f"Review by {today + timedelta(days=1)}\n")
    stale = tmp_path / "stale.md"
    expired = today - timedelta(days=1)
    stale.write_text(f"Review by {expired}\n")
    assert check_consistency.main([str(clean)]) == 0
    assert check_consistency.main([str(clean), str(stale)]) == 1
    assert f"review date {expired} has passed" in capsys.readouterr().err
