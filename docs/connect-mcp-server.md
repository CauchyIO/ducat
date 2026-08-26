# Connect Claude Code to the Databricks SQL MCP server

The skill reads evidence through the Databricks-managed SQL MCP server, at
`https://<workspace-hostname>/api/2.0/mcp/sql`. The feature is in Public Preview, verified working
2026-08-24. It exposes three tools: `execute_sql` (reads and writes), `execute_sql_read_only`, and
`poll_sql_result`. Queries run asynchronously — a call returns `PENDING` with a statement ID, and
the poller returns the rows.

Build the read-only principal first: `create-read-only-principal.md`.

## Credential

Claude Code's MCP client sends a static bearer header, so the credential must be long-lived. An
OAuth access token lasts an hour, and the OAuth app route needs an account admin. A personal access
token minted by the principal *for itself* needs neither:

```sh
dbsp tokens create --json '{"lifetime_seconds":7776000,"comment":"cost-optimizer mcp"}'
```

This works because the principal holds `CAN_USE` on tokens. The value prints once.

## Configuration

`.mcp.json` carries no secret and no workspace identity — both arrive from the environment:

```json
{
  "mcpServers": {
    "databricks-sql": {
      "type": "http",
      "url": "${DATABRICKS_MCP_URL}",
      "headers": { "Authorization": "Bearer ${DATABRICKS_SP_TOKEN}" }
    }
  }
}
```

`.claude/settings.json` denies the read-write tool, so the boundary holds at the tool surface as
well as at the grant:

```json
{ "permissions": {
    "deny": ["mcp__databricks-sql__execute_sql"],
    "allow": ["mcp__databricks-sql__execute_sql_read_only",
              "mcp__databricks-sql__poll_sql_result"] } }
```

Store the token in the OS keychain and export both variables from your shell profile.

The first command prompts for a value and echoes nothing. **What to paste is the `token_value` from
the `tokens create` output above** — the string beginning `dapi`, not the `token_id` beside it, and
not a passphrase of your own. It asks twice. Note this is a *different* credential from the `dose`
secret held under `databricks-cost-optimizer-sp`: same identity, two credentials, because this
client sends a static bearer token while an OAuth secret mints tokens that expire hourly.

```sh
security add-generic-password -a "$USER" -s databricks-cost-optimizer-pat -w
export DATABRICKS_MCP_URL="https://<workspace-hostname>/api/2.0/mcp/sql"
export DATABRICKS_SP_TOKEN="$(security find-generic-password -a "$USER" -s databricks-cost-optimizer-pat -w)"
```

Confirm the keychain holds the token rather than something else:

```sh
security find-generic-password -a "$USER" -s databricks-cost-optimizer-pat -w | cut -c1-4
```

That should print `dapi`.

Claude Code reads these from the environment of the process that launched it, so start it from a
shell where both are set. Approve the project server once, then `/mcp` should report `connected`
with three tools.

## Warehouse selection

The Databricks docs pin a warehouse with a `_meta.warehouse_id` parameter, reachable only from agent
code, not from a client's MCP config. It does not matter: the server picks a warehouse the caller
may use, and the principal has `CAN_USE` on exactly one. Selection is deterministic by permission.

## When it fails

Check the credential before anything else — an empty or malformed bearer token surfaces as a generic
connection error, naming nothing.

```sh
echo "len=${#DATABRICKS_SP_TOKEN}"; echo "${DATABRICKS_SP_TOKEN:0:4}"    # expect 38 and dapi
```

A one-character value means a stray shell comment reached the keychain prompt. Delete the entry,
re-add it, and paste the token alone.
