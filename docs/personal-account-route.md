# The personal-account route: reading as yourself through the CLI

Two routes reach a workspace. This runbook covers the default: the Databricks CLI, authenticated as
you, from a profile you choose. The safe alternative is the service principal through the managed
SQL MCP server, where Unity Catalog holds the read-only boundary and the principal cannot write
whatever a session intends. Both run the same packaged queries and return the same evidence. What
this route does not have is a platform boundary — the account can do whatever its grants allow,
writes included.

The skill offers the choice before it reads anything, presents this route as the default whenever
a valid CLI profile exists, and carries this warning whenever it is on offer:

> ⚠️ **Warning:** On this route the session runs as you, through the Databricks CLI, with every
> privilege your account holds. If your account can create, resize or delete compute, so can this
> session. It changes your workspace only when you ask for a named change, but that rule is written
> instruction in this package, not something the platform enforces. Your own permissions, and
> nothing else, are the boundary.

Nothing is read until you have chosen the route and named the profile. The skill then names the
route in one line you can quote back.

## Prerequisites

Three things, and the second is the one most people lack.

1. **The Databricks CLI, authenticated against the workspace.** Install it per the principal
   runbook, then log in once per workspace:

   ```sh
   databricks auth login --host https://<workspace-hostname> --profile <profile>
   ```

   `databricks auth profiles` lists what you have and whether each token is still valid. The skill
   presents that list and you pick; it never selects a profile for you, and it never touches a
   production profile you did not name.

2. **Read on the system catalog, held by your own account.** A workspace admin typically holds
   `MANAGE` on the `system` catalog, which permits administering it and reads nothing. Reading
   needs `USE_CATALOG`, `USE_SCHEMA` and `SELECT`, the same three the principal runbook grants to
   the principal. Check before you start:

   ```sql
   SELECT count(*) AS rows FROM system.billing.usage WHERE usage_date >= current_date() - 7
   ```

   The check passes when it returns a count. `INSUFFICIENT_PRIVILEGES` on `USE SCHEMA` means the
   grant is missing. Granting it is a write in the workspace, and the skill makes it only if you
   ask for that grant by name. We recommend you run the principal runbook's catalog grant with your own account as the principal, in your
   own admin session, and weigh the same caveat, that the catalog-level grant is wider than the
   eleven tables the skill reads and includes the audit log.

3. **A SQL warehouse you may use.** The MCP server picks one for the principal; on this route the
   statement names it. `CAN_USE` on any warehouse is enough. The skill lists them and takes one
   that is running or can auto-resume, and tells you that assessment queries incur ordinary
   warehouse compute.

## The three CLI calls

Three CLI calls carry the whole route. Every one is a direct `databricks` command, so before each
one runs Claude Code shows you the exact command and waits for you to approve or refuse it.

**Find a warehouse:**

```sh
databricks warehouses list --profile <profile> -o json
```

**Run a packaged query**, through the statement-execution API. The SQL is exactly what the MCP
route runs; only the warehouse id is added:

```sh
databricks api post /api/2.0/sql/statements --profile <profile> --json '{
  "warehouse_id": "<warehouse-id>",
  "wait_timeout": "50s",
  "statement": "SELECT ... FROM system.billing.usage WHERE ... LIMIT 200"
}'
```

**Poll a statement that came back `PENDING`:**

```sh
databricks api get /api/2.0/sql/statements/<statement-id> --profile <profile>
```

These three calls, and not a notebook, a SQL connector or a Python script, because they add no
dependency and put no code between you and the query: the statement-execution API takes the same
SQL text the MCP route runs, so a figure from the CLI route and one from the MCP route can be
compared line for line. That comparison is what proves the route, and it is still owed for one
confirmed scope.

## What stops a write on this route

`.claude/settings.json` lists `databricks` under `allow`, so CLI commands run without a prompt.
Nothing in configuration tells a read from a write. The skill changes your workspace only when you
ask for a named change, and that rule is instruction, not configuration. That is why the warning
ends the way it does: on this route your own permissions, and nothing else, are the boundary.

## When it fails

**Every system schema refuses with insufficient privileges.** Your account lacks the read grant
above. The correct behaviour, and what the skill does, is to say what it cannot read, decline to
grant itself access, and return to the route choice: the service principal, if available, or stop.
A skill that fixed the grant from inside the session would have written to your workspace on the
one route where nothing stops it.

**A direct call is refused with no prompt at all.** A deny rule is in force — most often a clone
of this repository still carrying the older `.claude/settings.json`, which denied `databricks`
outright. The skill stops on that refusal rather than working around it. Check which directory the
session started in.

**The MCP server is connected as well.** Nothing wrong: this route stays the default, and the route
is yours to choose. What must not happen is a `databricks-sql` call after the choice. A chosen route is never
mixed; asking to switch mid-assessment returns you to the route choice.

## Proving the route

The route is proven the way the MCP route is, by [`smoke-check.md`](smoke-check.md): one job, one
week, the cost source and the run history reconciled. Run checks 2 to 5 through the CLI as yourself
and compare each figure with the same check run as the principal. Until that comparison exists for
one confirmed scope, this route is documented, not proven.
