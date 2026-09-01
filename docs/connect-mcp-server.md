# Connect Claude Code to the Databricks SQL MCP server

The skill reads evidence through the Databricks-managed SQL MCP server at
`https://<workspace-hostname>/api/2.0/mcp/sql`. Queries run asynchronously: a call returns `PENDING`
with a statement ID, and a second call returns the rows.

Build the read-only principal first — [`create-read-only-principal.md`](create-read-only-principal.md).
This runbook assumes `dbsp` works and `WORKSPACE_URL` is exported. If in a fresh terminal, redo steps 0, 1, and 6 of that runbook.

## 1. Mint a token

Claude Code's MCP client sends a static bearer header, so the credential must be long-lived. An
OAuth access token lasts an hour; a personal access token minted by the principal for itself lasts
as long as you ask.

```sh
dbsp tokens create --json '{"lifetime_seconds":7776000,"comment":"cost-optimizer mcp"}'
```

The value prints once. This is a **different credential** from the `dose` secret stored in step 6 of
[`create-read-only-principal.md`](create-read-only-principal.md): same identity, two credentials,
because this client needs a static token and that one mints hourly ones.

## 2. Store the token

The prompt echoes nothing and asks twice. **What to paste is the `token_value` field from the output
above** — the string beginning `dapi`, not the `token_id` beside it, and not a passphrase of your
own.

macOS:

```sh
security add-generic-password -a "$USER" -s databricks-cost-optimizer-pat -w
```

Linux:

```sh
secret-tool store --label="databricks cost optimizer token" service databricks-cost-optimizer-pat account "$USER"
```

Windows (PowerShell):

```powershell
Set-Secret -Name databricks-cost-optimizer-pat
```

Confirm the store holds what you meant:

```sh
security find-generic-password -a "$USER" -s databricks-cost-optimizer-pat -w | cut -c1-4
```

That should print `dapi`.

## 3. Export the two variables

Claude Code reads these from the environment of the process that launched it, so they must be set in
the shell you start it from — not in your shell profile, which would make them global and permanent.

```sh
export DATABRICKS_MCP_URL="https://$WORKSPACE_URL/api/2.0/mcp/sql"
```

```sh
export DATABRICKS_SP_TOKEN="$(security find-generic-password -a "$USER" -s databricks-cost-optimizer-pat -w)"
```

## 4. Take the two configuration files

Copy both from this repository rather than retyping them.

`.mcp.json` defines the server. It carries no secret and no workspace identity — both arrive from
the variables you just exported.

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

`.claude/settings.json` denies the tools the skill must not use: the read-write MCP tool
`execute_sql`, and the Databricks CLI, which the skill never needs because it reads everything as
SQL. It allows `execute_sql_read_only` and `poll_sql_result`.

## 5. Verify

In the shell where you exported the variables, start Claude Code from the directory holding `.mcp.json` — it reads that file from the working directory and expands `${…}` from that shell's environment. Approve the project server when prompted, then type `/mcp` at the Claude Code prompt:

```
/mcp
```

**The verification passes when** `databricks-sql` is listed as connected with three tools. After verification is complete, run the checks in [`smoke-check.md`](smoke-check.md).

The server picks a warehouse the caller may use, and the principal has `CAN_USE` on exactly one, so
you do not choose one here.

## Potential causes of failure

### Wrong credential

Check the credential first. An empty or malformed bearer token surfaces as a generic connection
error naming nothing.

```sh
echo "len=${#DATABRICKS_SP_TOKEN}  starts=${DATABRICKS_SP_TOKEN:0:4}"
```

Expect a length around 38 and `dapi`. A length of 0 means the store lookup failed. A length of 1
means a stray character reached the prompt — delete the entry, add it again, and paste the token
alone.

### MCP server missing

If the server is missing from `/mcp` entirely, you started Claude Code somewhere other than the
directory holding `.mcp.json`, or in a shell where the variables were not set.
