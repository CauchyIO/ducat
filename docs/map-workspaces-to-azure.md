# Map workspaces to Azure

Azure Databricks bills through Azure. Joining cloud cost back to Databricks objects runs through
each workspace's **managed resource group** — the resource group Databricks creates and fills with
the VMs, disks, public IPs and NAT a workspace consumes. Without that key, Azure cost is a lump sum
you cannot attribute.

## Requirements

- **Azure CLI**, which can be installed using one of the methods below, depending on your operating
  system. If you encounter any difficulties, you can read the official Microsoft instructions
  [here](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli).
  - macOS: `brew install azure-cli`.
  - Windows: `winget install Microsoft.AzureCLI`.
  - Linux: `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`.
- **A subscription selected, not just a tenant.** `az login` can leave you at tenant scope, and the
  cost commands then return nothing without reporting a failure.
- **Cost Management Reader** on every subscription in the map, or a role that contains it. Resource
  Graph needs only read access to the workspaces; cost figures need this as well.

Prove both before assessing anything.

The first confirms you are scoped to a subscription rather than a tenant, and prints the account you
are signed in as:

```sh
az account show --query "{sub:name, id:id, user:user.name}" -o table
```

**Passes when** it names a subscription. If it prints nothing, `az login` left you at tenant scope
and every cost command below returns empty without reporting a failure. The `id` column is the
`<subscription-id>` the next command needs.

The second asks Cost Management for this subscription's month-to-date total — the smallest query
that exercises the same permission the assessment will need:

```sh
az rest --method post \
  --url "https://management.azure.com/subscriptions/<subscription-id>/providers/Microsoft.CostManagement/query?api-version=2024-08-01" \
  --body '{"type":"ActualCost","timeframe":"MonthToDate","dataset":{"granularity":"None","aggregation":{"total":{"name":"Cost","function":"Sum"}}}}'
```

**Passes when** the response carries a number. A `403` means Cost Management Reader is missing. A
`429` means throttling — wait a minute and repeat; it is not a permission failure.

**What skipping this costs.** Every figure stays labelled list cost. That is honest, and it is
permanent: a billed figure cannot be added to a finished assessment, because the reasoning was built
on the plane that answered. Recovering one means running the assessment again.

## The Databricks half

One query lists every workspace the metastore knows about. This is the inventory the Azure half has
to reconcile against:

```sql
SELECT workspace_id, workspace_name, workspace_url, status
FROM system.access.workspaces_latest
ORDER BY create_time
```

**Returns** one row per workspace, oldest first. Keep `workspace_id` — it is the join key to the
Azure half, and the only column that survives a rename or a move.

**Note:** This table does **not** carry: any Azure resource ID, subscription, or resource group. It
lists workspaces and nothing about where they live. The Azure half has to come from Azure.

Cancelled workspaces disappear from this table, so a workspace that billed earlier in the period may
not appear at all. Reconcile against `system.billing.usage` grouped by `workspace_id` rather than
assuming the inventory is complete.

## The Azure half

Resource Graph returns the Azure half — subscription, resource group and managed resource group
per workspace — for every subscription you can read, in one call. The first line installs the
extension and is needed only once:

```sh
az extension add --name resource-graph
az graph query -q "resources
  | where type =~ 'microsoft.databricks/workspaces'
  | project name,
            workspaceId = tostring(properties.workspaceId),
            workspaceUrl = tostring(properties.workspaceUrl),
            managedResourceGroup = tostring(properties.managedResourceGroupId),
            resourceGroup, subscriptionId, tenantId, location" -o table
```

`properties.workspaceId` is the join key: it equals `workspace_id` in the system tables. Match on
that rather than on name — workspace names are not unique across subscriptions, and `workspaceUrl`
changes if a workspace moves.

Without Azure access, the portal shows the same facts one workspace at a time: **Overview →
Managed Resource Group**, with the subscription in the breadcrumb.

## Verify before using it

Count both sides. The workspaces returned by Resource Graph must reconcile with those in
`system.access.workspaces_latest`; a shortfall means a workspace sits in a subscription the caller
cannot read, and the map is incomplete rather than small.

Do not infer a managed resource group from its name. The default is
`databricks-rg-<workspace>-<hash>`, but it can be set to anything at creation — in the first estate
mapped this way, one workspace used a short custom name matching no convention at all. Read the
property; never pattern-match it.

## What the map is for

It sizes the access request. One cost-reader grant is needed per subscription holding a workspace in
scope, or one at a management group covering them all. Record which subscriptions were granted and
which were not — an ungranted subscription is reported as list-price only, never quietly dropped.

The map also exposes regional structure. A workspace whose SKUs carry a different region suffix from
your metastore bills into the same account while its runtime detail stays invisible to your queries.
Name that workspace in the map so the gap is a known boundary rather than a surprise.
