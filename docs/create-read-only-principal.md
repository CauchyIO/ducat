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
- Unity Catalog system schemas already carrying rows.

Account admin is **not** required. Granting on individual `system` schemas is, which is why step 3
grants on the catalog instead.

## 1. Create the principal

```sh
databricks service-principals create \
  --json '{"displayName":"sp-databricks-cost-optimizer","active":true}'
```

Keep both IDs it returns: `applicationId` is the OAuth client ID, `id` is the SCIM ID used by the
admin APIs. It arrives with `workspace-access` and `databricks-sql-access` and no groups but `users`.

## 2. Allow it to hold tokens

```sh
export SP=<applicationId>

databricks token-management update-permissions --json "{\"access_control_list\":[
  {\"service_principal_name\":\"$SP\",\"permission_level\":\"CAN_USE\"}]}"
```

## 3. Grant read on the system catalog

```sh
databricks grants update CATALOG system \
  --json "{\"changes\":[{\"principal\":\"$SP\",\"add\":[\"USE_CATALOG\",\"USE_SCHEMA\",\"SELECT\"]}]}"
```

Catalog level, because per-schema grants on `system` are refused to anyone but an account admin.
This reads wider than the skill needs — `system.access.audit` included — so narrowing it later is
worth an issue.

Never add the principal to a group holding `MANAGE` on `system`. `MANAGE` permits granting.

## 4. Give it one warehouse

```sh
databricks warehouses update-permissions <warehouse-id> --json "{\"access_control_list\":[
  {\"service_principal_name\":\"$SP\",\"permission_level\":\"CAN_USE\"}]}"
```

`update-permissions` merges; `set-permissions` replaces. Check the existing owner survived.

## 5. Issue a credential

Azure Databricks has no on-behalf-of token API — that endpoint is AWS and GCP only. Use the
workspace secrets proxy, which a workspace admin may call for any principal in the workspace:

```sh
databricks service-principal-secrets-proxy create <scim-id> --lifetime 7776000s
```

The secret prints once. Record its ID and expiry locally; never the secret itself.

## 6. Reach it from your shell

`DATABRICKS_*` environment variables outrank any profile, so exporting them globally makes every
command run as the principal. Scope them to one command instead. macOS:

```sh
security add-generic-password -a "$USER" -s databricks-cost-optimizer-sp -w   # prompts, no history

dbsp() {
  DATABRICKS_HOST="https://<workspace-hostname>" \
  DATABRICKS_CLIENT_ID="<applicationId>" \
  DATABRICKS_CLIENT_SECRET="$(security find-generic-password -a "$USER" -s databricks-cost-optimizer-sp -w)" \
  databricks "$@"
}
```

On Windows, a dedicated `[cost-optimizer-sp]` profile in `.databrickscfg` invoked with `-p` gives
the same separation.

## 7. Verify

```sh
dbsp auth describe        # must print oauth-m2m and the applicationId, not your user
```

If it prints your own account, every probe below tests you instead of the principal. That mistake
produced a false pass here once.

```sh
dbsp api post /api/2.0/sql/statements --json '{
  "warehouse_id":"<warehouse-id>",
  "statement":"SELECT count(*) FROM system.billing.usage WHERE usage_date > current_date() - 7",
  "wait_timeout":"30s"}'          # expect a row count

dbsp api post /api/2.0/sql/statements --json '{
  "warehouse_id":"<warehouse-id>",
  "statement":"CREATE TABLE <catalog>.default.write_probe (x INT)",
  "wait_timeout":"30s"}'          # expect state FAILED, PERMISSION_DENIED
```

Then sweep the privileges the principal actually holds. Read **effective** privileges, not direct
grants — direct grants hide everything inherited from a group:

```sh
databricks grants get-effective CATALOG <catalog> --principal $SP
databricks grants get-effective SCHEMA <catalog>.<schema> --principal $SP
```

## Incomplete

The write probe currently **succeeds**, so this guide is not finished.

Databricks grants every workspace principal create rights on the workspace catalog's `default`
schema, through an automatic `_workspace_users_<catalog>_<workspace-id>` group. The principal
inherits `CREATE_TABLE` there. Unity Catalog has no `DENY`, so it cannot be patched over.

Remaining steps:

1. Remove the `workspace-access` entitlement and re-check whether implicit membership follows it.
   `databricks service-principals patch <scim-id> --json '{"Operations":[{"op":"remove","path":"entitlements[value eq \"workspace-access\"]"}],"schemas":["urn:ietf:params:scim:api:messages:2.0:PatchOp"]}'`
2. If it does not, ask the catalog owner to revoke those defaults from the group.
3. Re-run the effective-privilege sweep and the write probe, and record both.
4. Ask an account admin to narrow `SELECT` on `system` to the five schemas the skill reads.
5. Rotate the secret once the MCP client is wired.
