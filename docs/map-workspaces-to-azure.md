# Map workspaces to Azure

Do this only if you want billed cost rather than list cost, or want to see the Azure resources a
workspace consumes on its own — the NAT gateway, public IP and disks that Databricks never reports.
Everything else in this skill works without it.

Azure bills those resources into a **managed resource group**, one per workspace, and nothing in the
Databricks system tables names it. This runbook produces that mapping and grants the access that
makes the figures readable.

## 1. Install the Azure CLI and sign in

macOS:

```sh
brew install azure-cli
```

Windows:

```powershell
winget install Microsoft.AzureCLI
```

Linux:

```sh
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

Then sign in and select a subscription. Signing in can leave you at tenant scope, where the cost
commands return nothing and report no failure.

```sh
az login
```

```sh
az account show --query "{sub:name, id:id, user:user.name}" -o table
```

**Passes when** the output names a subscription rather than showing nothing.

## 2. List the workspaces from Databricks

```sql
SELECT workspace_id, workspace_name, workspace_url, status
FROM system.access.workspaces_latest
ORDER BY create_time
```

This table names workspaces and nothing about where they live in Azure — no resource id, no
subscription, no resource group. Step 3 supplies that half.

Cancelled workspaces disappear from this table, so a workspace that billed earlier in the period may
be missing entirely. Compare against `system.billing.usage` grouped by `workspace_id` before
treating the list as complete.

## 3. List the same workspaces from Azure

```sh
az extension add --name resource-graph
```

```sh
az graph query -q "resources
  | where type =~ 'microsoft.databricks/workspaces'
  | project name,
            workspaceId = tostring(properties.workspaceId),
            workspaceUrl = tostring(properties.workspaceUrl),
            managedResourceGroup = tostring(properties.managedResourceGroupId),
            resourceGroup, subscriptionId, tenantId, location" -o table
```

Join the two lists on `workspaceId`, which equals `workspace_id` from step 2. Match on that rather
than on name: workspace names are not unique across subscriptions, and the URL changes if a
workspace moves.

Never guess a managed resource group from its name. The default looks like
`databricks-rg-<workspace>-<hash>`, but whoever created the workspace can set it to anything, and in
the first estate mapped this way one workspace used a short custom name matching no convention at
all. Read the property.

**Passes when** every workspace from step 2 appears with a managed resource group. A workspace
missing here sits in a subscription you cannot read, so the map is incomplete rather than short.

## 4. Get cost-reader access on each subscription

Ask for **Cost Management Reader** on every subscription holding a workspace in the map, or once at
a management group covering them all. Step 3 needed only read access to the workspaces; reading cost
needs this as well.

Confirm it works before relying on it:

```sh
az rest --method post \
  --url "https://management.azure.com/subscriptions/<subscription-id>/providers/Microsoft.CostManagement/query?api-version=2024-08-01" \
  --body '{"type":"ActualCost","timeframe":"MonthToDate","dataset":{"granularity":"None","aggregation":{"total":{"name":"Cost","function":"Sum"}}}}'
```

**Passes when** the response contains a number.

A `403` means the role has not been granted. A `429` means the API is throttling you — wait a minute
and run it again, because throttling is not a permission failure and reads like one.

Record which subscriptions were granted and which were not. A workspace in an ungranted subscription
is reported as list cost only, and saying so is better than quietly leaving it out.
