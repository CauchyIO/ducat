"""Tests for hooks/refuse-writes.py, the PreToolUse hook that holds the read-only boundary."""

import io
import json
from pathlib import Path
from types import ModuleType

import pytest

HOOKS = Path(__file__).resolve().parent.parent / "hooks"


@pytest.fixture(scope="session")
def refuse_writes() -> ModuleType:
    """The hook script, loaded once for the whole run, the way conftest loads tools/."""
    path = HOOKS / "refuse-writes.py"
    module = ModuleType("refuse-writes")
    module.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
    return module


@pytest.mark.parametrize(
    "tool",
    [
        "mcp__plugin_ducat_databricks-sql__execute_sql",  # installed as a plugin
        "mcp__databricks-sql__execute_sql",  # the project-level .mcp.json, as before
    ],
)
def test_read_write_tool_is_denied_under_either_namespace(refuse_writes, tool):
    """`execute_sql` is refused whether the server arrived through the plugin or a project."""
    decision, _ = refuse_writes.decide(tool, {"query": "SELECT 1"})
    assert decision == "deny"


@pytest.mark.parametrize("tool", ["execute_sql_read_only", "poll_sql_result"])
def test_read_tools_are_allowed(refuse_writes, tool):
    """The two read-only tools are approved, so a confirmed scope is not re-asked per query."""
    decision, _ = refuse_writes.decide(f"mcp__plugin_ducat_databricks-sql__{tool}", {})
    assert decision == "allow"


@pytest.mark.parametrize(
    "command",
    [
        "dbsp tokens create",
        "echo hi; dbsp auth describe",
        "ls | dbsp auth token",
        "set -e\ndbsp tokens list",
    ],
)
def test_service_principal_wrapper_is_denied_in_any_segment(refuse_writes, command):
    """`dbsp` belongs to neither route, so it is refused wherever it appears as a command."""
    decision, reason = refuse_writes.decide("Bash", {"command": command})
    assert decision == "deny"
    assert "dbsp" in reason


@pytest.mark.parametrize(
    "command",
    [
        "databricks clusters list",
        "cd /tmp && databricks jobs list",
        "ls | databricks fs cp -",
        "set -e\ndatabricks warehouses list",
    ],
)
def test_databricks_cli_asks_in_any_segment(refuse_writes, command):
    """The CLI is the personal-account route's transport, so every call asks the user first."""
    decision, reason = refuse_writes.decide("Bash", {"command": command})
    assert decision == "ask"
    assert "databricks" in reason


@pytest.mark.parametrize(
    "command",
    [
        "echo databricks",  # the word as an argument, not a command
        "cat docs/databricks-notes.md",
        "grep -n dbsp docs/connect-mcp-server.md",
        "git status",
    ],
)
def test_other_bash_commands_pass_through(refuse_writes, command):
    """Mentioning the CLI is not invoking it; the ordinary permission flow runs."""
    assert refuse_writes.decide("Bash", {"command": command}) is None


def test_unrelated_tools_pass_through(refuse_writes):
    """A tool outside the matcher's intent gets no opinion from the hook."""
    assert refuse_writes.decide("Read", {"file_path": "x"}) is None
    assert refuse_writes.decide("mcp__other__execute_sql_read_only", {}) is None


def test_main_emits_decision_json_and_exits_zero(refuse_writes, monkeypatch, capsys):
    """A denial travels in the stdout JSON, with exit 0, per Claude Code's hook contract."""
    event = {"tool_name": "Bash", "tool_input": {"command": "dbsp tokens create"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event)))
    assert refuse_writes.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"


def test_main_emits_ask_for_the_cli(refuse_writes, monkeypatch, capsys):
    """The CLI travels the same JSON contract, carrying `ask` rather than `deny`."""
    event = {"tool_name": "Bash", "tool_input": {"command": "databricks clusters list"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event)))
    assert refuse_writes.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_main_is_silent_when_it_has_no_opinion(refuse_writes, monkeypatch, capsys):
    """No decision means no output at all, so nothing else is disturbed."""
    event = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event)))
    assert refuse_writes.main() == 0
    assert capsys.readouterr().out == ""


def test_main_survives_malformed_input(refuse_writes, monkeypatch, capsys):
    """Garbage on stdin never blocks a tool: exit 0 and no output."""
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert refuse_writes.main() == 0
    assert capsys.readouterr().out == ""
