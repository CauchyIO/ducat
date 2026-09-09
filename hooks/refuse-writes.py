"""Hold the read-only boundary the skill's .claude/settings.json used to hold.

A plugin cannot ship permission rules, so the denials, the ask and the allowances that
lived in `.claude/settings.json` become a PreToolUse hook. It runs before any tool on
the `databricks-sql` MCP server and before any Bash command, and decides:

    deny   the read-write MCP tool `execute_sql`, however the server is namespaced;
    deny   a Bash command that invokes `dbsp`, the service-principal wrapper, whose
           identity reaches a workspace through the MCP server rather than a shell;
    ask    before a Bash command that invokes the Databricks CLI (`databricks`), the
           transport of the personal-account route, which runs as the user;
    allow  `execute_sql_read_only` and `poll_sql_result`, so a confirmed scope is not
           re-asked per query, as SKILL.md's preflight section requires;
    pass   anything else, leaving the ordinary permission flow untouched.

Enforcement in configuration is the second line, never the first. On the service-principal
route the first is Unity Catalog: the principal holds read on system tables and CAN_USE on
one warehouse, so a write is refused by the platform whatever the model intends. The
personal-account route has no such platform line — the user's own permissions bound it —
which is why the CLI asks rather than passing silently. This hook applies only where the
plugin is loaded, it sees only the command string, and no static rule catches an alias
someone invents or a script that shells out to the CLI.

The hook prints Claude Code's PreToolUse decision JSON on stdout and always exits 0.
"""

import json
import re
import sys

READ_TOOLS = ("execute_sql_read_only", "poll_sql_result")
WRITE_TOOL_RX = re.compile(r"databricks-sql__execute_sql$")
# A command word at the start of the line or of a shell segment (after ; & | or newline).
SP_WRAPPER_RX = re.compile(r"(?:^|[;&|\n]\s*)dbsp(?=\s|$)")
CLI_RX = re.compile(r"(?:^|[;&|\n]\s*)databricks(?=\s|$)")


def decide(tool_name: str, tool_input: dict[str, object]) -> tuple[str, str] | None:
    """Maps one tool call to a permission decision.

    Args:
        tool_name: The fully qualified tool name Claude Code is about to call, e.g.
            `mcp__plugin_ducat_databricks-sql__execute_sql` or `Bash`.
        tool_input: The tool's input object; for Bash, `command` is the shell line.

    Returns:
        A `(decision, reason)` pair where decision is `"deny"`, `"ask"` or `"allow"`, or
        None when the hook has no opinion and the ordinary permission flow should run.
    """
    if WRITE_TOOL_RX.search(tool_name):
        return (
            "deny",
            "execute_sql reads and writes; DUCAT is read-only and uses "
            "execute_sql_read_only for every query. Its absence is deliberate.",
        )
    if "databricks-sql__" in tool_name and tool_name.endswith(READ_TOOLS):
        return ("allow", "Read-only Databricks SQL tool; scope confirmation authorises it.")
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if isinstance(command, str):
            if SP_WRAPPER_RX.search(command):
                return (
                    "deny",
                    "`dbsp` runs as the service principal, and that identity reaches a workspace "
                    "through the MCP server. It belongs to neither access route.",
                )
            if CLI_RX.search(command):
                return (
                    "ask",
                    "`databricks` is the transport of the personal-account route, and it runs as "
                    "you, with every privilege your account holds. Approve only the call you "
                    "intend: the read-only rule is written instruction in this package, not "
                    "something the platform enforces.",
                )
    return None


def main() -> int:
    """Reads the PreToolUse event from stdin and prints the decision, if any.

    Returns:
        0 always. A denial is carried in the JSON on stdout, not in the exit code, so a
        malformed event can never block an unrelated tool.
    """
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        return 0

    verdict = decide(tool_name, tool_input)
    if verdict is None:
        return 0
    decision, reason = verdict
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
