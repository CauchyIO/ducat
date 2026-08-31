# Create a read-only service principal

The managed Databricks SQL MCP server runs whatever SQL it is given, reads and writes alike,
governed only by Unity Catalog permissions. The skill's read-only boundary therefore has to live in
the identity it connects as, not in its instructions. This is how that identity is built.

Values for a specific workspace — hostname, principal IDs, warehouse ID — belong in a local,
untracked note, not here.

## Requirements

- Databricks CLI. macOS: `brew tap databricks/tap && brew install databricks`. Windows:
  `winget install Databricks.DatabricksCLI`. Linux:
  `curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh`.
- A workspace admin login: `databricks auth login --host https://<workspace-hostname>`.
  `<workspace-hostname>` is the address bar of your browser while you are in the workspace, with
  `https://` and everything after the first `/` removed.
- Unity Catalog system schemas already carrying rows.

Account admin is **not** required. Granting on individual `system` schemas is, which is why step 3
grants on the catalog instead.

## 0. Set the workspace address

Everything below runs in one shell. Export the workspace address first — it is the address bar of
your browser while you are in the workspace, with `https://` and everything after the first `/`
removed.

```sh
export WORKSPACE_URL=<workspace-hostname>
```

## 1. Create the principal

```sh
databricks service-principals create \
  --json '{"displayName":"sp-databricks-cost-optimizer","active":true}'
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

The principal arrives with `workspace-access` and `databricks-sql-access`, and no groups but `users`.

## 2. Allow it to hold tokens

```sh
databricks token-management update-permissions --json "{\"access_control_list\":[
  {\"service_principal_name\":\"$SP\",\"permission_level\":\"CAN_USE\"}]}"
```

## 3. Grant read on the system catalog

```sh
databricks grants update CATALOG system \
  --json "{\"changes\":[{\"principal\":\"$SP\",\"add\":[\"USE_CATALOG\",\"USE_SCHEMA\",\"SELECT\"]}]}"
```

Catalog level, because granting on individual `system` schemas is refused to anyone but an account
admin — holding `MANAGE` on the catalog is not enough.

The grant is read-only and wider than the eleven tables the skill names: it also reaches
`system.access.audit`, the lineage tables and the network logs. Reading them changes nothing, and
for most setups the simplicity is worth more than the precision. If least privilege matters where
you are deploying this, the appendix has the narrower version and who has to run it.

Never add the principal to a group holding `MANAGE` on `system`. `MANAGE` permits granting.

## 4. Give it one warehouse

The principal needs somewhere to execute SQL. System tables are readable from any warehouse in the
workspace — the warehouse is compute, not a data source, and has no relationship to what is being
assessed. List them and copy an ID:

```sh
databricks warehouses list
```

Choose a small serverless one, and **not** a warehouse you intend to assess: the assessment's own
queries would start it, add billed minutes and change the idle profile being measured.

Export its ID — the value of the `id` column in the output above.

```sh
export WAREHOUSE_ID=<the id field of the warehouse you chose>
```

```sh
databricks warehouses update-permissions $WAREHOUSE_ID --json "{\"access_control_list\":[
  {\"service_principal_name\":\"$SP\",\"permission_level\":\"CAN_USE\"}]}"
```

Grant exactly one. The MCP server picks a warehouse the caller may use, so a second grant makes the
choice arbitrary rather than deterministic.

`update-permissions` merges; `set-permissions` replaces. Check the existing owner survived.

## 5. Issue a credential

Azure Databricks has no on-behalf-of token API — that endpoint is AWS and GCP only. Use the
workspace secrets proxy, which a workspace admin may call for any principal in the workspace:

`$SCIM` is the `id` field exported in step 1 — not `$SP`, which is the `applicationId`. Passing the
wrong one returns an error that does not say which field it wanted.

```sh
databricks service-principal-secrets-proxy create $SCIM --lifetime 7776000s
```

The secret prints once. Record its ID and expiry locally; never the secret itself.

## 6. Reach it from your shell

Two things happen in this step. The secret goes into your operating system's credential store, so it
never appears in a file or in your shell history. Then a wrapper called `dbsp` runs any Databricks
command as the principal by reading the secret back out, one command at a time.

The wrapper matters because `DATABRICKS_*` environment variables outrank any profile: exporting them
globally would make *every* command run as the principal, including ones you meant to run as
yourself. `databricks …` stays you, `dbsp …` is the principal.

**What to paste when prompted is the `secret` field from step 5's output** — the long string
beginning `dose`, not the `id` or the `secret_hash` beside it, and not a passphrase of your own. The
prompt echoes nothing and asks twice.

### macOS

Store it — `security` calls whatever it holds a "password"; here that word means the secret:

```sh
security add-generic-password -a "$USER" -s databricks-cost-optimizer-sp -w
```

Then define the wrapper:

```sh
dbsp() {
  : "${WORKSPACE_URL:?set it in step 0}" "${SP:?set it in step 1}"
  DATABRICKS_AUTH_TYPE="oauth-m2m" \
  DATABRICKS_HOST="https://$WORKSPACE_URL" \
  DATABRICKS_CLIENT_ID="$SP" \
  DATABRICKS_CLIENT_SECRET="$(security find-generic-password -a "$USER" -s databricks-cost-optimizer-sp -w)" \
  databricks "$@"
}
```

### Linux

Store it with `secret-tool`, from `libsecret-tools`. This one reads the secret from your typing
rather than prompting twice:

```sh
secret-tool store --label="databricks cost optimizer" service databricks-cost-optimizer-sp account "$USER"
```

Then define the wrapper:

```sh
dbsp() {
  : "${WORKSPACE_URL:?set it in step 0}" "${SP:?set it in step 1}"
  DATABRICKS_AUTH_TYPE="oauth-m2m" \
  DATABRICKS_HOST="https://$WORKSPACE_URL" \
  DATABRICKS_CLIENT_ID="$SP" \
  DATABRICKS_CLIENT_SECRET="$(secret-tool lookup service databricks-cost-optimizer-sp account "$USER")" \
  databricks "$@"
}
```

### Windows, PowerShell

Store it with the `Microsoft.PowerShell.SecretManagement` and `SecretStore` modules, installing them
first if you have not:

```powershell
Set-Secret -Name databricks-cost-optimizer-sp
```

Then define the wrapper:

```powershell
function dbsp {
  $env:DATABRICKS_AUTH_TYPE     = "oauth-m2m"
  $env:DATABRICKS_HOST          = "https://$env:WORKSPACE_URL"
  $env:DATABRICKS_CLIENT_ID     = $env:SP
  $env:DATABRICKS_CLIENT_SECRET = Get-Secret -Name databricks-cost-optimizer-sp -AsPlainText
  databricks @args
}
```

Unlike the shell versions this leaves the variables set in the session, so open a fresh window when
you want to run a command as yourself again.

### Confirm what was stored

Before relying on it, check the store holds what you meant. On macOS:

```sh
security find-generic-password -a "$USER" -s databricks-cost-optimizer-sp -w | cut -c1-4
```

That should print `dose`. Anything else — a stray character, a pasted comment, the `id` instead of
the `secret` — means the entry is wrong, and the failure surfaces later as an authentication error
naming no cause.

## 7. Verify

Four checks. Run all of them — a half-verified principal is one you cannot make claims about.

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
account, the credential did not load and every check below tests you instead of the principal. That
mistake produced a false pass here once.

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

One write right survives all of this, and it is not a misconfiguration.

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

## Appendix: a narrower grant

Only an account admin can run these; a workspace admin with `MANAGE` on the catalog is refused with
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
