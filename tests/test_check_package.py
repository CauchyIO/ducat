"""Tests for tools/check-package.py, the credential and estate-identifier scanner."""

from pathlib import Path

import pytest

# Built at runtime on purpose: check-package.py scans this file too, and a literal
# credential shape here would fail the CI job that guards the repository.
DAPI = "dapi" + "0" * 32
DOSE = "dose" + "0" * 32
JWT = ".".join(["eyJ" + "a" * 12, "b" * 12, "c" * 12])
PRIVATE_KEY = "-----BEGIN " + "RSA PRIVATE KEY-----"
ASSIGNED = "client_secret" + " = " + "x" * 24
HOSTNAME = "adb-" + "1234567890" + ".12.azuredatabricks.net"
GUID = "12345678-1234-1234-1234-123456789012"
WAREHOUSE = "0123456789abcdef"


def rules(findings: list[str]) -> set[str]:
    """Pull the rule names out of finding strings shaped `path:line: rule: match`."""
    return {f.split(": ")[1] for f in findings}


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        (DAPI, "databricks-token"),
        (DOSE, "databricks-oauth-secret"),
        (JWT, "json-web-token"),
        (PRIVATE_KEY, "private-key"),
        (ASSIGNED, "assigned-secret"),
    ],
)
def test_credentials_refused_everywhere(check_package, tmp_path: Path, text, rule):
    """Each credential shape is caught even in a file outside the client-facing package."""
    f = tmp_path / "scratch.md"
    f.write_text(f"some prose then {text} then more\n")
    assert rule in rules(check_package.scan(str(f)))


@pytest.mark.parametrize(
    "text",
    [
        "dapi" + "0" * 31,  # one character short
        "dapi" + "g" * 32,  # not hex
        "eyJ" + "a" * 12 + "." + "b" * 12,  # only two JWT segments
        "-----BEGIN " + "CERTIFICATE-----",  # a key block that is not private
        "password: hunter2",  # assigned, but too short to be a real secret
        "the password policy requires twenty characters",  # the word, no assignment
    ],
)
def test_credential_near_misses_stay_silent(check_package, tmp_path: Path, text):
    """Shapes one step away from a credential are not flagged.

    False alarms teach people to reach for check-allow, so the boundary has to hold from
    the other side too.
    """
    f = tmp_path / "scratch.md"
    f.write_text(text + "\n")
    assert check_package.scan(str(f)) == []


@pytest.mark.parametrize(
    "assignment",
    [
        "client-secret: " + "x" * 20,
        "PASSWORD = " + "x" * 20,
        "api_key=" + "x" * 20,
        "access_token = '" + "x" * 20 + "'",
    ],
)
def test_assigned_secret_accepts_each_key_and_separator(check_package, tmp_path: Path, assignment):
    """The assigned-secret rule covers every key name it lists, either separator, any case."""
    f = tmp_path / "scratch.md"
    f.write_text(assignment + "\n")
    assert rules(check_package.scan(str(f))) == {"assigned-secret"}


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        (HOSTNAME, "workspace-hostname"),
        ("1234567890123456", "workspace-id"),
        (GUID, "guid"),
        (WAREHOUSE, "warehouse-id"),
    ],
)
def test_identifiers_refused_only_in_package(
    check_package, tmp_path: Path, monkeypatch, text, rule
):
    """Each identifier shape is caught under docs/ and ignored in a working directory.

    A workspace id in a scratch note is nobody's problem; the same id in a runbook is
    what a client reads. The scanner has to tell those two locations apart.
    """
    monkeypatch.chdir(tmp_path)
    for d in ("docs", "scratch"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "note.md").write_text(f"id {text}\n")
    assert rule in rules(check_package.scan("docs/note.md"))
    assert check_package.scan("scratch/note.md") == []


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("SKILL.md", True),
        ("references/opportunities/job.md", True),
        ("docs/runbook.md", True),
        ("tools/check-package.py", False),
        ("environment.local.md", False),
    ],
)
def test_in_package(check_package, path, expected):
    """The package boundary is the fixed list of roots a client reads, nothing else."""
    assert check_package.in_package(path) is expected


@pytest.mark.parametrize(
    "text",
    [
        "12345678901234",  # 14 digits: too short for a workspace id
        "12345678-1234-1234-1234-12345678901",  # GUID with a short last group
        "adb-1234567.1.azuredatabricks.net",  # hostname with too few digits
    ],
)
def test_identifier_near_misses_stay_silent(check_package, tmp_path: Path, monkeypatch, text):
    """Numbers and names one step away from an identifier shape are not flagged, even in-package."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text(text + "\n")
    assert check_package.scan("docs/note.md") == []


def test_scanner_skips_its_own_source(check_package, monkeypatch):
    """The scanner's own file is skipped: its private-key pattern matches its own source.

    Run from the repository root, the way the hook and CI run it.
    """
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    assert check_package.main(["tools/check-package.py"]) == 0


def test_check_allow_exempts_the_line(check_package, tmp_path: Path):
    """A line marked check-allow is skipped, and only that line."""
    f = tmp_path / "scratch.md"
    f.write_text(f"{DAPI}  <!-- check-allow: fake, documented above -->\n{DOSE}\n")
    findings = check_package.scan(str(f))
    assert len(findings) == 1
    assert findings[0].startswith(f"{f}:2:")


def test_clean_and_unreadable_files_yield_nothing(check_package, tmp_path: Path):
    """Clean text, a binary blob and a missing path all produce no findings."""
    clean = tmp_path / "clean.md"
    clean.write_text("nothing to see\n")
    binary = tmp_path / "blob.bin"
    binary.write_bytes(b"\xff\xfe\x00\x01")
    assert check_package.scan(str(clean)) == []
    assert check_package.scan(str(binary)) == []
    assert check_package.scan(str(tmp_path / "missing.md")) == []


def test_main_exit_codes(check_package, tmp_path: Path, capsys):
    """Exit 0 when nothing is found, 1 with the rule named on stderr when something is.

    Directories passed on the command line are skipped rather than failing the run.
    """
    clean = tmp_path / "clean.md"
    clean.write_text("fine\n")
    dirty = tmp_path / "dirty.md"
    dirty.write_text(DAPI + "\n")
    assert check_package.main([str(clean), str(tmp_path)]) == 0
    assert check_package.main([str(clean), str(dirty)]) == 1
    assert "databricks-token" in capsys.readouterr().err
