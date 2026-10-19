# Getting started

From a workspace nobody has prepared to the skill installed and querying system tables as you, through the Databricks CLI, in the order the steps have to happen. That is the default route. The service principal is the safe alternative, and its setup follows as an optional section. Each step links the runbook that carries the detail; this page exists so nobody has to infer the sequence from a folder listing.

Budget an hour of your own work for a workspace nobody has prepared. Access you have to request sits outside that hour and rarely arrives within it: a grant on the `system` catalog if your account lacks one, an account admin if you need the narrower grant, a cost role on the Azure subscriptions if Azure cost is in scope.

## Before you start

Prior to beginning the set up and installation, please make sure to satisfy the following criteria:

- Install **Databricks CLI** and authenticate it against the workspace as yourself. Installation is
  in [`create-read-only-principal.md`](create-read-only-principal.md); the login command is in
  [`personal-account-route.md`](personal-account-route.md).
- **Read on the `system` catalog, held by your own account,** and `CAN_USE` on a SQL warehouse.
  Step 2 checks both.
- **The Azure CLI**, if Azure cost is in scope. Decide that now rather than later; the requirements
  and the check are in [`map-workspaces-to-azure.md`](map-workspaces-to-azure.md).
- **A Unity Catalog** workspace whose system schemas are enabled and carrying rows. Step 1 checks
this before anything is built, because an empty schema means waiting for data rather than fixing
a permission.

## The sequence

**1. Confirm the evidence exists.** Run check 1 of [`smoke-check.md`](smoke-check.md) as yourself —
one query, five row counts and freshness dates. Nothing has been built yet, and nothing should be
until this passes: a schema present but empty means backfill, not a permissions problem.

**2. Check your own access.** Your account needs read on the `system` catalog and a warehouse it
may use. The prerequisites in [`personal-account-route.md`](personal-account-route.md) carry the
one-query check and what to do when the grant is missing.

**3. Install the skill.** Symlink the repository into your skills directory; the root
[`README`](../README.md) has the command and additional instructions. The skill offers the CLI route
first, with a warning, before it reads anything.

**If Azure cost is in scope:** map each workspace to its subscription and managed resource
group. Databricks cannot see per-workspace networking cost, and that is where an idle workspace
hides. See [`map-workspaces-to-azure.md`](map-workspaces-to-azure.md).

**Note:** Settle the Azure question before the first assessment, not after it. Without Azure cost access every
figure the skill produces is labelled list cost and stays that way: the assessment reasoned from the
sources it could read, and a billed figure cannot be added to a finished document — recovering one
means running the assessment again.

## Optional: the service-principal route

The safe alternative. A principal with read grants only cannot write, whatever the session intends,
so Unity Catalog holds the boundary rather than an instruction. It needs workspace admin rights to
build; account admin is needed only for the narrower grant, and the runbook says so where it applies.

**A. Build the read-only identity.** A dedicated service principal, read on the `system` catalog,
one warehouse, and a credential — plus the workspace-catalog exception you will inherit and cannot
remove. See [`create-read-only-principal.md`](create-read-only-principal.md).

**B. Connect the client.** The managed SQL MCP server, a token, and configuration that carries
neither secret nor workspace identity. See [`connect-mcp-server.md`](connect-mcp-server.md).

**C. Prove the path end to end.** Checks 2 to 5 of [`smoke-check.md`](smoke-check.md), now run as
the principal through the connection: one job, one week, reconciled against its run history. The
cheapest evidence that credential, warehouse, transport and tables all work together.

## You are done when

- A query returns rows through the CLI, authenticated as you.
- The skill offers the CLI route first, with its warning, before it reads anything.

If you set up the service-principal route as well:

- A query returns rows through the MCP tool, authenticated as the principal rather than as you.
- A write is refused by Unity Catalog, not merely declined by the model.
- The smoke check reconciles, and every discrepancy has a named cause.

## When something behaves oddly

Almost every setup problem here is an identity problem: a command running as you when you expected
the principal, or the reverse. Check with `dbsp auth describe`, which must print `oauth-m2m` for the authentication method and the principal's application ID as the user. If it prints your own account, the credential did not load, and everything you ran through the wrapper measured your own access rather than the principal's.

The next most common is a rate limit mistaken for a permission failure. Azure Cost Management
returns `429` on a second query within a minute, with a `Retry-After` header saying how long to
hold off; it means wait, not forbidden.
