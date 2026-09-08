# Create a read-only service principal

The managed Databricks SQL MCP server runs whatever SQL it is given, reads and writes alike,
governed only by Unity Catalog permissions. The skill's read-only boundary therefore has to live in
the identity it connects as, not in its instructions. This is how that identity is built.

Values for a specific workspace — hostname, principal IDs, warehouse ID — belong in a local,
untracked note, not here.

## Requirements

- Databricks CLI, which can be installed using one of the methods below, depending on your operating system. If you encounter any difficulties, you can read the official Databricks instructions [here](https://docs.databricks.com/aws/en/dev-tools/cli/install).
  - macOS: `brew tap databricks/tap && brew install databricks`.
  - Windows: `winget install Databricks.DatabricksCLI`
  - Linux: `curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh`.
- A workspace admin login: `databricks auth login --host https://<workspace-hostname>`.
  `<workspace-hostname>` is the address bar of your browser while you are in the workspace, with
  `https://` and everything after the first `/` removed.
- Unity Catalog system schemas enabled on the metastore and already carrying rows. Enablement is an
  account-admin action, per metastore, and rows accrue only from that point on — so a recently
  enabled metastore may answer a query and still hold too little history to cost anything.

Account admin is **not** required. Granting on individual `system` schemas is, which is why step 3
grants on the catalog instead.

## 0. Set the workspace address

**All of the steps in this runbook are to be executed in one shell.** Export the workspace address
first — it is the address bar of your browser while you are in the workspace, with `https://` and
everything after the first `/` removed.

**Example.** The digits below are invented rather than taken from any workspace, which is why the
two lines carrying them are exempt from `tools/check-package.py`. An address bar reading

`https://adb-8271946503728461.11.azuredatabricks.net/explore/data?o=8271946503728461` <!-- check-allow -->

makes `WORKSPACE_URL` the hostname alone — `https://` and everything from the first `/` onward
removed, including the `?o=` repeat of the workspace id:

`adb-8271946503728461.11.azuredatabricks.net` <!-- check-allow -->

```sh
export WORKSPACE_URL=<workspace-hostname>
```

You can verify that it exported properly by printing the value in your terminal:

```sh
echo $WORKSPACE_URL
```

This should print the workspace URL value that you assigned.

## 1. Create the principal

```sh
databricks service-principals create \
  --json '{"displayName":"sp-ducat","active":true}'
```

The output contains two fields you need, and they are easy to confuse. `applicationId` is the OAuth
client ID. `id` is the SCIM ID used by the admin APIs. Export both now, in the same shell, so no
later step asks you to find them again.

```sh
export SP=<the applicationId field from the output above>
```

```sh
export SCIM=<the id field from the output above>
```

As before, you can verify that both of these exported properly by printing the values in the terminal:

```sh
echo $SP && echo $SCIM
```

This should print the service principal application ID and the SCIM ID that you assigned.

The principal arrives with `workspace-access` and `databricks-sql-access`, and no groups but `users`.

## 2. Allow it to hold tokens

Creating a personal access token is a workspace permission in its own right — without it the principal can authenticate but cannot mint one, which is what c[`connect-mcp-server.md`](connect-mcp-server.md) step 1 needs it to do. `CAN_USE` grants that, and `update-permissions` adds the principal to the existing access control list rather than replacing it; `set-permissions` takes the same JSON and would revoke everyone else's token access in the same call.

```sh
databricks token-management update-permissions --json "{\"access_control_list\":[
  {\"service_principal_name\":\"$SP\",\"permission_level\":\"CAN_USE\"}]}"
```

## 3. Grant read on the system catalog

This is the grant that makes the principal useful and keeps it harmless. `USE_CATALOG` and `USE_SCHEMA` permit traversal only — they expose no rows — and `SELECT` is the one privilege that reads any; no write follows from the three. As in step 2, update with add extends the catalog's existing grants rather than replacing them.

```sh
databricks grants update CATALOG system \
  --json "{\"changes\":[{\"principal\":\"$SP\",\"add\":[\"USE_CATALOG\",\"USE_SCHEMA\",\"SELECT\"]}]}"
```

The target is the catalog, not the individual schemas, because per-schema grants on system are refused to anyone but an account admin — holding `MANAGE` on the catalog is not enough.

The grant is read-only and wider than the eleven tables the skill names: it also reaches
`system.access.audit`, the lineage tables and the network logs. Reading them changes nothing, and
for most setups the simplicity is worth more than the precision. If least privilege matters where
you are deploying this, the appendix has the narrower version and who has to run it.

Never add the principal to a group holding `MANAGE` on `system`. `MANAGE` permits granting and revoking privileges on the catalog and everything under it, transferring ownership, and renaming — and a principal that can grant can grant to itself, which undoes every boundary set above.

## 4. Give it one warehouse

The principal needs somewhere to execute SQL. System tables are readable from any warehouse in the
workspace — the warehouse is compute, not a data source, and has no relationship to what is being
assessed. List them and copy the ID from the one you want to use:

```sh
databricks warehouses list
```

Choose a small serverless one, and **not** a warehouse you intend to assess: the assessment's own
queries would start it, add billed minutes and change the idle profile being measured.

Export its ID — the value of the `id` column in the output above.

```sh
export WAREHOUSE_ID=<the id field of the warehouse you chose>
```

You can verify that it exported properly using:

```sh
echo $WAREHOUSE_ID
```

This should print the warehouse ID that you selected.

`CAN_USE` lets the principal run queries on this warehouse, starting it if it is idle; it does not permit resizing, stopping, or reconfiguring it. Grant it on this warehouse only — the MCP server picks a warehouse the caller may use, so holding exactly one grant is what makes that choice deterministic rather than something you configure. `update-permissions` merges here as it did in step 2.

```sh
databricks warehouses update-permissions $WAREHOUSE_ID --json "{\"access_control_list\":[
  {\"service_principal_name\":\"$SP\",\"permission_level\":\"CAN_USE\"}]}"
```

## 5. Issue a credential

Azure Databricks has no on-behalf-of token API — that endpoint is AWS and GCP only. Use the
workspace secrets proxy, which a workspace admin may call for any principal in the workspace:

```sh
databricks service-principal-secrets-proxy create $SCIM --lifetime 7776000s
```

**Note**: `$SCIM` is the `id` field exported in step 1 — not `$SP`, which is the `applicationId`. Passing the
wrong one returns an error that does not say which field it wanted.

The secret prints once and cannot be retrieved again — step 6 pastes it straight into your credential store, so keep the output on screen until then. Your local note records its ID and expiry only; never the secret itself.

## 6. Reach it from your shell

Two things happen in this step:

1. The secret goes into your operating system's credential store, so it never appears in a file or in your shell history.
2. A wrapper called `dbsp` runs any Databricks command as the principal by reading the secret back out, one command at a time.

The wrapper matters because `DATABRICKS_*` environment variables outrank any profile: exporting them
globally would make *every* command run as the principal, including ones you meant to run as
yourself. `databricks …` stays you, `dbsp …` is the principal.

**What to paste when prompted is the `secret` field from step 5's output** — the long string
beginning `dose`, not the `id` or the `secret_hash` beside it, and not a passphrase of your own. The
prompt echoes nothing and asks twice.

### macOS

Store it. The command says `add-generic-password`, but security calls everything it stores a password — here that means the `dose` secret from step 5:

```sh
security add-generic-password -a "$USER" -s ducat-sp -w
```

Then define the wrapper:

```sh
dbsp() {
  : "${WORKSPACE_URL:?set it in step 0}" "${SP:?set it in step 1}"
  DATABRICKS_AUTH_TYPE="oauth-m2m" \
  DATABRICKS_HOST="https://$WORKSPACE_URL" \
  DATABRICKS_CLIENT_ID="$SP" \
  DATABRICKS_CLIENT_SECRET="$(security find-generic-password -a "$USER" -s ducat-sp -w)" \
  databricks "$@"
}
```

### Linux

Store it with `secret-tool`, from `libsecret-tools`. This one reads the secret from your typing
rather than prompting twice:

```sh
secret-tool store --label="ducat" service ducat-sp account "$USER"
```

Then define the wrapper:

```sh
dbsp() {
  : "${WORKSPACE_URL:?set it in step 0}" "${SP:?set it in step 1}"
  DATABRICKS_AUTH_TYPE="oauth-m2m" \
  DATABRICKS_HOST="https://$WORKSPACE_URL" \
  DATABRICKS_CLIENT_ID="$SP" \
  DATABRICKS_CLIENT_SECRET="$(secret-tool lookup service ducat-sp account "$USER")" \
  databricks "$@"
}
```

### Windows (PowerShell)

Store it with the `Microsoft.PowerShell.SecretManagement` and `SecretStore` modules, installing them
first if you have not:

```powershell
Set-Secret -Name ducat-sp
```

Then define the wrapper:

```powershell
function dbsp {
  $env:DATABRICKS_AUTH_TYPE     = "oauth-m2m"
  $env:DATABRICKS_HOST          = "https://$env:WORKSPACE_URL"
  $env:DATABRICKS_CLIENT_ID     = $env:SP
  $env:DATABRICKS_CLIENT_SECRET = Get-Secret -Name ducat-sp -AsPlainText
  databricks @args
}
```

**Note:** Unlike the shell versions this leaves the variables set in the session, so open a fresh window when
you want to run a command as yourself again.

### Confirm what was stored

Before relying on it, check the store holds what you meant. macOS:

```sh
security find-generic-password -a "$USER" -s ducat-sp -w | cut -c1-4
```

Linux:

```sh
secret-tool lookup service ducat-sp account "$USER" | cut -c1-4
```

Windows (PowerShell):

```powershell
(Get-Secret -Name ducat-sp -AsPlainText).Substring(0,4)
```

That should print `dose`. Anything else — a stray character, a pasted comment, the `id` instead of
the `secret` — means the entry is wrong, and the failure surfaces later as an authentication error
naming no cause.

## 7. Verify

Four checks, one for each property this setup claims:

1. The connection is the principal and not you.
2. It can read the evidence.
3. It cannot write.
4. It holds nothing beyond what you granted.

If you skip one, then that property is asserted rather than shown.

First, name a catalog the principal was never granted anything on. `databricks catalogs list` shows
one owner per catalog; pick any owned by a person or a team rather than by a `_workspace_admins_…`
group, because that last one is your workspace catalog and it behaves differently.

```sh
export GOVERNED_CATALOG=<the name of a catalog the principal has no grant on>
```

### Check 1 — the wrapper runs as the principal

```sh
dbsp auth describe
```

**Passes when** it prints `oauth-m2m` and the `applicationId` from step 1. If it prints your own
account or `databricks-cli` as the authentication methof, then the credential did not load and every check below tests you instead of the principal. That mistake produced a false pass here once.

### Check 2 — the principal can read system tables

```sh
dbsp api post /api/2.0/sql/statements --json '{
  "warehouse_id":"'$WAREHOUSE_ID'",
  "statement":"SELECT count(*) FROM system.billing.usage WHERE usage_date > current_date() - 7",
  "wait_timeout":"30s"}'
```

**Passes when** the response carries a row count.

### Check 3 — the principal cannot write

```sh
dbsp api post /api/2.0/sql/statements --json '{
  "warehouse_id":"'$WAREHOUSE_ID'",
  "statement":"CREATE TABLE '$GOVERNED_CATALOG'.default.write_probe (x INT)",
  "wait_timeout":"30s"}'
```

**Passes when** the response is `state: FAILED` with `PERMISSION_DENIED` and SQLSTATE `42501`.

A refusal here is the read-only boundary demonstrated rather than asserted. Nothing is created, so
there is nothing to clean up.

### Check 4 — the principal holds only what you granted

The two commands below print **effective** privileges: everything the principal can do, including
whatever it inherits from a group. `databricks grants get` shows only privileges granted directly,
and would miss exactly the surprises this check exists to find.

```sh
databricks grants get-effective CATALOG system --principal $SP
```

**Passes when** it lists `USE_CATALOG`, `USE_SCHEMA` and `SELECT`, and nothing else.

```sh
databricks grants get-effective CATALOG $GOVERNED_CATALOG --principal $SP
```

**Passes when** it lists nothing, or `BROWSE` alone. Anything more means the principal inherited
access to real data through a group, and the grant needs tracing before you go further.

## The workspace-catalog exception

One write permission survives all of this, and it is not a misconfiguration.

Every Databricks workspace has a catalog named after itself, and every principal in the workspace
can create tables in that catalog's `default` schema. The right arrives through an automatic
`_workspace_users_…` group whose membership is implicit and system-managed. Unity Catalog has no
`DENY`, and removing the `workspace-access` entitlement does not change it. The only way to take it
away is to revoke the grant from every user of the workspace.

Do not. It disrupts colleagues for the sake of one scratch schema, and a client workspace will not
permit it — a design that depends on doing so does not travel.

This is why check 3 probes a governed catalog rather than the workspace one. Against the workspace
catalog the create would succeed, and the check would look like a failure of the boundary when it is
a property of the platform.

What the principal ends up with: read on `system`, `BROWSE` or nothing on every governed catalog,
`CAN_USE` on one warehouse, and create rights confined to the workspace catalog's `default` schema.
It cannot read data in a governed catalog, modify any existing object anywhere, or reach a job,
cluster or warehouse beyond running queries on the one it was given.

## A narrower grant (account admin only)

**Only an account admin can run the commands below**; a workspace admin with `MANAGE` on the catalog is refused with
`User is not an account admin for Account`. Ask for this where least privilege matters — a client
engagement, a shared workspace, an estate whose audit log is sensitive. Otherwise step 3 is enough.

Traversal only at the catalog:

```sh
databricks grants update CATALOG system \
  --json "{\"changes\":[{\"principal\":\"$SP\",\"add\":[\"USE_CATALOG\"]}]}"
```

The four schemas the skill reads whole — every table in them is cost or infrastructure telemetry:

```sh
for S in billing compute lakeflow query; do
  databricks grants update SCHEMA system.$S \
    --json "{\"changes\":[{\"principal\":\"$SP\",\"add\":[\"USE_SCHEMA\",\"SELECT\"]}]}"
done
```

`access` holds eight tables and the skill needs one. Traverse the schema:

```sh
databricks grants update SCHEMA system.access \
  --json "{\"changes\":[{\"principal\":\"$SP\",\"add\":[\"USE_SCHEMA\"]}]}"
```

Then read only `workspaces_latest`, leaving `audit` and the lineage tables unreadable:

```sh
databricks grants update TABLE system.access.workspaces_latest \
  --json "{\"changes\":[{\"principal\":\"$SP\",\"add\":[\"SELECT\"]}]}"
```

Add these before removing the wide grant from step 3. While both are held Unity Catalog takes the
union, so nothing is exposed that was not already; revoking first breaks the connection if a grant
is refused.

Then verify: one table read from each schema, and `SELECT * FROM system.access.audit LIMIT 1`
failing with `42501`. A narrowing nobody tested is a narrowing nobody has.
