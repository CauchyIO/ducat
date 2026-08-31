# Getting started

Setting this up end to end, in order. Each step links the runbook that carries the detail; this page
exists so nobody has to infer the sequence from a folder listing.

Budget an hour for a workspace nobody has prepared, most of it waiting on other people.

## Before you start

- **The Databricks CLI**, authenticated against the workspace. Installation is in step 2's runbook.
- **Workspace admin.** You do not need account admin, and the runbooks say where that matters.
- **The Azure CLI**, if Azure cost is in scope. Decide that now rather than later; the requirements
  and the check are in [`map-workspaces-to-azure.md`](map-workspaces-to-azure.md).
- **A Unity Catalog workspace** whose `system` schemas carry rows. Databricks enables them centrally
  now, so this is a check rather than a task — confirm before assuming a gap.

## The sequence

**1. Confirm the evidence exists.** Run check 1 of [`smoke-check.md`](smoke-check.md) as yourself —
one query, five row counts and freshness dates. Nothing has been built yet, and nothing should be
until this passes: a schema present but empty means backfill, not a permissions problem.

**2. Build the read-only identity.** A dedicated service principal, read on the `system` catalog,
one warehouse, and a credential — plus the workspace-catalog exception you will inherit and cannot
remove. [`create-read-only-principal.md`](create-read-only-principal.md)

**3. Connect the client.** The managed SQL MCP server, a token, and configuration that carries
neither secret nor workspace identity. [`connect-mcp-server.md`](connect-mcp-server.md)

**4. Prove the path end to end.** Checks 2 to 5 of [`smoke-check.md`](smoke-check.md), now run as
the principal through the connection: one job, one week, reconciled against its run history. The
cheapest evidence that credential, warehouse, transport and tables all work together.

**5. Install the skill.** Symlink the repository into your skills directory; the root
[`README`](../README.md) has the command.

**Only if Azure cost is in scope:** map each workspace to its subscription and managed resource
group. Databricks cannot see per-workspace networking cost, and that is where an idle workspace
hides. [`map-workspaces-to-azure.md`](map-workspaces-to-azure.md)

Settle that question before the first assessment, not after it. Without the Azure plane every figure
the skill produces is labelled list cost and stays that way, and a billed figure cannot be added to a
finished document — the assessment reasoned from the plane it could read, so recovering one means
running it again.

## You are done when

- A query returns rows through the MCP tool, authenticated as the principal rather than as you.
- A write is refused by Unity Catalog, not merely declined by the model.
- The smoke check reconciles, and every discrepancy has a named cause.

## When something behaves oddly

Almost every setup problem here is an identity problem: a command running as you when you expected
the principal, or the reverse. [`identity-and-credentials.md`](identity-and-credentials.md) covers
which identity resolves, why environment variables outrank profiles, and how to undo an override.

The second most common is a rate limit read as a permission failure. Azure Cost Management returns
`429` on a second query within a minute; it means wait, not forbidden.
