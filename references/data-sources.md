# Data sources

Evidence semantics for the preflight and baseline stages. Read this before the scope type matters.

Distilled 2026-08-21 from the Databricks cost component matrix, the Databricks cost tracking guide,
the 2026-07-01 pricing reassessment findings, and FOCUS v1.4 (see `NOTICE.md`).

## Contents

- [Precedence](#precedence)
- [Sources and what each supports](#sources-and-what-each-supports)
- [Turning usage into cost](#turning-usage-into-cost)
- [Executing through the MCP server](#executing-through-the-mcp-server)
- [Telling a service apart from the price it bills on](#telling-a-service-apart-from-the-price-it-bills-on)
- [Tying a cost to the scope that caused it](#tying-a-cost-to-the-scope-that-caused-it)
- [Cost bases and FOCUS vocabulary](#cost-bases-and-focus-vocabulary)
- [Evidence invariants](#evidence-invariants)
- [Freshness](#freshness)
- [Fallbacks](#fallbacks)

## Precedence

One ordering governs every evidence plane. Higher rung wins a disagreement:

1. live read-only Databricks system tables, queried as SQL;
2. live read-only Azure Cost Management, Resource Graph and pricing APIs, reached through the Azure
   CLI;
3. current official Databricks and Microsoft documentation;
4. user-provided exports;
5. explicitly limited estimates.

Business constraints sit outside the ladder — they come from the user and have no fallback. So does
packaged practice material, including this file: it seeds the analysis and never outranks rungs 1–3
on a mutable vendor fact.

## Sources and what each supports

| Evidence | Where it comes from | What it supports |
|---|---|---|
| Databricks usage | `system.billing.usage` | Usage quantity, SKU, product, resource, identity, tag attribution |
| Historical published cost | Date-valid `system.billing.list_prices` | Historical list cost, normalized comparisons |
| Per-statement attribution | `system.billing.attributed_usage` | DBSQL statement-level DBUs, query tags, executing identity. Empty in some accounts — check before designing around it |
| Workload behaviour | `system.lakeflow.*`, `system.compute.*`, `system.query.history`, serving telemetry | Runtime, failures, utilization, schedules, consumers, performance |
| Object configuration | `system.compute.*` and `system.lakeflow.*`, as slowly-changing dimensions | Settings as they were during the period, carrying `change_time`. A live API returns only what is true now |
| Actual Azure cost | Cost Management actual or amortized data | Billed cost, discounts, classic infrastructure, invoice reconciliation |
| Azure attribution | Resource Graph, resource tags | Resource identity, region, ownership, tag context |
| Forward pricing | Official Databricks pricing, Azure Retail Prices API | Target-state counterfactuals |
| Practice guidance | `opportunity-catalog.md` plus current official docs | Mechanisms, constraints, current product behaviour |
| Business constraints | User confirmation | Required outcomes, risk tolerance, ownership, feasibility |

Starting authorities — follow successor pages when Microsoft moves them, and record retrieval dates:

- [Monitor costs using Azure Databricks system tables](https://learn.microsoft.com/en-us/azure/databricks/admin/usage/system-tables)
- [Billable usage system table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing)
- [Pricing system table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/pricing)
- [Monitor job costs and performance](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost)
- [Actual and amortized Azure cost data](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/review-subscription-billing)
- [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)

**System tables have no SLA.** Data typically lands hours after the usage. They are an accounting
source, not an operational one — never present a system-table figure as real-time.

**Azure Cost Management throttles hard.** A second query within a minute returns HTTP 429. Put every
grouping you need into one query rather than looping over scopes, and back off in minutes rather
than seconds. A 429 is a rate limit, not an access problem — do not read it as missing permission.

## Turning usage into cost

Cost is not stored anywhere. `system.billing.usage` records quantities — DBUs, gigabytes, storage
units — and `system.billing.list_prices` records what one unit cost during a given price period.
Every figure this skill reports is the product of the two, so every figure depends on matching each
usage record to the price that was valid at the moment the usage happened.

```sql
SELECT
  u.billing_origin_product,
  u.sku_name,
  sum(u.usage_quantity)                                     AS dbus,
  sum(u.usage_quantity * lp.pricing.effective_list.default) AS list_cost,
  sum(CASE WHEN lp.pricing.effective_list.default IS NULL
           THEN u.usage_quantity ELSE 0 END)                AS unpriced_quantity
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON  lp.cloud         = u.cloud
  AND lp.sku_name      = u.sku_name
  AND lp.usage_unit    = u.usage_unit
  AND lp.currency_code = :currency
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= :period_start
  AND u.usage_date <  :period_end
GROUP BY ALL
ORDER BY list_cost DESC NULLS FIRST
LIMIT 50
```

Compose your own version of this query rather than copying it, and keep all three conditions in the
`ON` clause. Each one is doing a job, and dropping any of them produces a total that looks
reasonable and is wrong.

The join is a `LEFT JOIN` deliberately. Tightening a join loses rows as readily as it inflates them:
under an inner join, a usage record matching no price row does not appear as zero — it leaves the
result entirely, and the total prints normally without it. Keep every condition in the `ON` clause
for the same reason. Moving any of them to a later `WHERE` filters on the price table after the
join and quietly restores the inner-join behaviour.

**Condition 1 — the three join keys identify which price applies.**

```sql
ON  lp.cloud      = u.cloud
AND lp.sku_name   = u.sku_name
AND lp.usage_unit = u.usage_unit
```

A price is published per cloud, per SKU and per unit of measure, so all three are needed to find the
right row. Matching on the SKU alone can pair a usage record with a price belonging to another cloud
or another unit.

**Condition 2 — `currency_code` stops the same price being counted twice.**

```sql
AND lp.currency_code = :currency
```

`list_prices` holds one row per currency for every price period, so an account that publishes in
more than one currency will match each usage record two or three times over. The cost then doubles
or triples without anything failing.

The filter belongs in the join rather than in a later `WHERE`, and under a left join that placement
is what separates the two failures. In the `ON` clause, usage carrying no price in this currency
survives as an unpriced row you can count. In a `WHERE`, it is dropped, and the total prints without
it.

**Condition 3 — the validity window matches usage to the price that applied at the time.**

```sql
AND u.usage_end_time >= lp.price_start_time
AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
```

Prices change, and `list_prices` keeps the old rows with `price_start_time` and `price_end_time`
marking when each was in force. Without `u.usage_end_time` bounded by those two columns, a SKU whose
price has changed matches every price it has ever had. `PREMIUM_JOBS_COMPUTE` has been $0.175, then
$0.350, and is now $0.300 — three rows, so every usage record for it would be counted three times.

The same window is what stops you pricing an old period at today's rate. A price change inside the
period being assessed is a real feature of that period, not an inconvenience to smooth over: valuing
2018 usage at the current rate would overstate it by 17%.

**Coverage — report what the join could not price.**

Report `unpriced_quantity` beside every cost figure and name the SKUs it came from. Unpriced usage
is usage whose price this query could not find, never usage that was free; missing records prove
nothing.

Where nothing prices at all, treat the query as failed rather than reporting a zero-cost finding.
The usual cause is `:currency`: an account publishing only in EUR returns no priced rows when
queried in USD. One estate priced Databricks usage in USD while Azure reported EUR, which is exactly
the situation that produces it. Any SKU absent from `list_prices` for the period — new, renamed, or
a region variant the table does not carry — drops out the same way.

## Executing through the MCP server

Queries reach Databricks through the managed SQL MCP server, using `execute_sql_read_only`. The
read-write tool on that server is denied by configuration; the identity behind it cannot write
either.

Two behaviours change how a query must be written:

**Results are truncated to protect the context window.** A truncated result looks exactly like a
complete one unless the `truncated` flag is checked. Never eyeball a row count and assume you have
the whole set — aggregate so the whole set is small.

**Execution is asynchronous.** A call returns a statement ID with `PENDING`; the result arrives from
`poll_sql_result`. A cold warehouse takes a minute or so, and that is a wait, not a failure.

What you group by is what decides how many rows come back, and a `LIMIT` will not save you: it cuts
the answer short rather than making it smaller. Grouping the query above by product and SKU returns
roughly a dozen rows for a whole period. Adding `usage_date`, to see the trend rather than the
total, returns one row per driver per day instead — 71 rows for a single week in a small account,
and several hundred over a month.

So ask for the period total first, and only then ask for a trend, and only on the one scope that
earned the attention. To break the total down by tag, job or warehouse, run a second query that
groups by those columns. Never fetch the individual usage rows and add them up afterwards: that is
the shape that gets truncated, and a truncated sum is wrong without announcing it.

Every packaged query therefore: aggregates in SQL, bounds its period to the confirmed scope,
orders by the measure that matters, and carries `LIMIT 100` or tighter. System tables also refuse
insufficiently selective queries outright — `System Table query returned too much data` is a
missing predicate, not an outage.

## Telling a service apart from the price it bills on

`billing_origin_product` says **what generated the cost**. `sku_name` says **how it is priced**.
Different dimensions. Many services have no SKU of their own and bill through another service's.

Join on `sku_name` to get a price. Group by `billing_origin_product` to understand a driver. Group
by SKU alone and Vector Search disappears into the serving line, while Predictive Optimization hides
inside serverless jobs — which is exactly how a background service escapes an assessment.

The names below are stems. A live `sku_name` carries a tier prefix and usually a region suffix, so
the stem `ALL_PURPOSE_SERVERLESS_COMPUTE` appears in the data as
`PREMIUM_ALL_PURPOSE_SERVERLESS_COMPUTE_EU_WEST`. Match with `LIKE` or on the stem's position within
the name, never on equality.

Observed mapping (matrix March 2026, corrected by the 2026-07-01 reassessment — verify live):

| `billing_origin_product` | `sku_name`(s) | Mechanics |
|---|---|---|
| `ALL_PURPOSE` | `ALL_PURPOSE_COMPUTE`, `ALL_PURPOSE_COMPUTE_(PHOTON)` | Classic cluster DBU |
| `INTERACTIVE` | `ALL_PURPOSE_SERVERLESS_COMPUTE`, `MODEL_TRAINING` | Serverless interactive; GPU work on the training SKU |
| `JOBS` | `JOBS_COMPUTE`, `JOBS_COMPUTE_(PHOTON)`, `JOBS_SERVERLESS_COMPUTE` | Classic or serverless jobs |
| `SQL` | `SQL_COMPUTE`, `SQL_PRO_COMPUTE`, `SERVERLESS_SQL_COMPUTE`, `JOBS_SERVERLESS_COMPUTE` | Warehouse compute; JOBS_SERVERLESS for DLT-backed streaming tables and MVs |
| `DLT` | `DLT_CORE_COMPUTE`, `DLT_PRO_COMPUTE`, `DLT_ADVANCED_COMPUTE`, `JOBS_SERVERLESS_COMPUTE` | Classic DLT on DLT SKUs; serverless DLT on JOBS_SERVERLESS |
| `MODEL_SERVING` | `SERVERLESS_REAL_TIME_INFERENCE`, `ANTHROPIC_MODEL_SERVING`, `OPENAI_MODEL_SERVING`, `GEMINI_MODEL_SERVING` | Custom models on the inference SKU; foundation models have their own. All four bill per DBU — pay-per-token endpoints are a different SKU family |
| `VECTOR_SEARCH` | `SERVERLESS_REAL_TIME_INFERENCE` + `JOBS_SERVERLESS_COMPUTE` | **Dual billing**: endpoint serving plus background index sync |
| `DATABASE` / `LAKEBASE` | `DATABASE_SERVERLESS_COMPUTE`, `DATABRICKS_STORAGE`, plus background maintenance on `JOBS_SERVERLESS_COMPUTE` | **Triple component**: compute, storage in DSUs, background jobs |
| `APPS` | `ALL_PURPOSE_SERVERLESS_COMPUTE` | Lakehouse Apps |
| `PREDICTIVE_OPTIMIZATION` | `JOBS_SERVERLESS_COMPUTE` | Background service, per catalog/schema |
| `DATA_QUALITY_MONITORING` | `JOBS_SERVERLESS_COMPUTE` | **Renamed** from `LAKEHOUSE_MONITORING` (~Feb 2026); old value now legacy |
| `AI_FUNCTIONS` | `SERVERLESS_REAL_TIME_INFERENCE` | Only `ai_parse_document`, `ai_extract`, `ai_classify`. **`ai_query` bills under `MODEL_SERVING`** as batch inference |
| `AI_GATEWAY`, `AGENT_EVALUATION` | `SERVERLESS_REAL_TIME_INFERENCE` | Own origin values, inference SKU |
| `DATA_CLASSIFICATION`, `FINE_GRAINED_ACCESS_CONTROL`, `BASE_ENVIRONMENTS` | `JOBS_SERVERLESS_COMPUTE` | Background platform services |
| `ONLINE_TABLES`, `LAKEFLOW_CONNECT` | `DLT_CORE_COMPUTE`, `DLT_PRO_COMPUTE`, `DLT_ADVANCED_COMPUTE`, `JOBS_SERVERLESS_COMPUTE` | Bill through the pipeline underneath |
| `AI_RUNTIME` | `ALL_PURPOSE_SERVERLESS_COMPUTE`, `JOBS_SERVERLESS_COMPUTE` | Serverless GPU pool |
| `FOUNDATION_MODEL_TRAINING` | `MODEL_TRAINING` | Fine-tuning |
| `NOTEBOOKS` | `ALL_PURPOSE_SERVERLESS_COMPUTE` | Distinct origin from `INTERACTIVE` |
| `CLEAN_ROOM` | `CLEAN_ROOMS_COLLABORATOR` | Flat per-DAY rate, not a DBU rate — never price it per hour |
| `NETWORKING` | `INTERNET_EGRESS_*`, `DATABRICKS_INTER_CONTINENTAL_EGRESS_*`, `PUBLIC_CONNECTIVITY_DATA_PROCESSED` | Per-GB by route; per-hour for private endpoints |
| `GENIE` | `GENIE` (from 2026-07-06) | Metered DBUs; underlying SQL compute still billed on top |

Other origins to expect: `DEFAULT_STORAGE`, `AGENT_BRICKS`, `DATA_SHARING`,
`EXTERNAL_COMPATIBILITY`. Enumerate what is actually present rather than assuming this list is
closed — always start a scan with `SELECT DISTINCT billing_origin_product`.

Newer attribution surfaces worth using: `usage_type`, `product_features` (`jobs_tier`, `sql_tier`,
`dlt_tier`, `is_serverless`, `is_photon`, `serving_type`), `identity_metadata`, and `usage_metadata`
subfields including `job_id`, `warehouse_id`, `dlt_pipeline_id`, `endpoint_name`, `notebook_id`,
`app_name`, `database_instance_id`, `budget_policy_id`.

## Tying a cost to the scope that caused it

**Check for a native identifier before offering a method.** `system.billing.usage` has a column
called `usage_metadata`, a struct whose subfields name the object that produced each record. Read a
subfield with dot notation:

```sql
SELECT usage_metadata.job_id, sum(usage_quantity)
FROM system.billing.usage
WHERE usage_metadata.job_id IS NOT NULL
GROUP BY ALL
```

The subfields worth reaching for are `job_id`, `warehouse_id`, `dlt_pipeline_id`, `endpoint_name`,
`app_name`, `notebook_id` and `database_instance_id`, among some fifty in total. Where one of them
covers the scope you are assessing, that is native attribution and the platform has already done the
work for you. Query for it first, offer it first, and label it native.

Three weaker methods exist for when no subfield of `usage_metadata` covers the scope: the
`custom_tags` column on the same table, matching objects by name, and a list of objects the user
supplies by hand. Do not offer these alongside a native identifier as though the choice were even —
a user given four options will sometimes pick a worse one than the evidence supports.

Label each mapping by the method that produced it, not by how confident it feels. Recording a native
mapping as manual weakens every figure built on it, because the confidence label decides where an
opportunity ranks in the shortlist, and the portfolio calculation reads those labels when it decides
which savings may be added together.

Decide which objects belong to the scope before aggregating anything, and report the four
populations separately rather than as one total:

| Population | Meaning |
|---|---|
| **Native** | A platform-generated `usage_metadata` subfield names the object directly on the billing record |
| **Manual** | A human asserted that a named object belongs to the scope — either by confirming it, or by tagging the object so the assertion is carried on the billing record itself as a `custom_tags` entry |
| **Inferred** | The object was matched by name or convention, with nothing on the record to confirm it. The weakest, and always labelled |
| **Unallocated** | Spend inside the period that matched no object. Report it as its own line; never spread it across the others |

Each situation below breaks attribution in a way the query cannot detect. Where one applies to the
scope, say so in the assessment rather than reporting the figure as though it were clean:

| Situation | Consequence |
|---|---|
| Cluster launched from a pool (Azure/AWS) | Cloud resources inherit pool and workspace tags only — cluster tags never reach the VMs, so Azure Cost Analysis cannot see them |
| Pool tag key collides with cluster tag key | Pool tag wins; the cluster tag is silently dropped on cloud resources |
| Custom tag key collides with a default | Custom key is prefixed `x_` |
| Job runs on all-purpose compute | No `job_id` on the billing record. Per-job attribution is impossible on shared all-purpose compute — this is a structural gap, not a query problem |
| Notebook runs inside a job | The job's serverless usage policy applies; the notebook's is ignored |
| Pipeline in development mode | Policy tag updates take up to 24 h to propagate |
| Workspace tag change | Up to 1 h to propagate; existing resources need a restart |
| Multiple policies assigned to one user | First alphabetically becomes the default |
| Query tags | Never in `system.billing.usage`. They reach `system.query.history`, and statement-level `system.billing.attributed_usage` where that table is populated — confirm it carries rows before relying on it |
| Unity Catalog tags | Governance only. They do not appear in billing usage |

Reserved keys that must not be used as custom tags: `Vendor`, `ClusterId`, `ClusterName`, `Creator`,
`Name`, `RunName`, `JobId`, `DatabricksInstancePoolId`, `DatabricksInstancePoolCreatorId`,
`SqlWarehouseId`, the `LakehouseMonitoring*` family, and the `budget-policy-*` family. Overriding
`Name` breaks cluster tracking and auto-termination — a tagging change that causes runaway cost.

Tags cannot be applied retroactively to historical billing records. A tagging improvement is a
prerequisite that improves future attribution, never a saving.

A resource serving several teams has to be split between them rather than assigned to one. For a
SQL warehouse, divide its cost in proportion to query execution time per team, taken from
`system.query.history`. Then report two things alongside the split: that execution time was the
basis for it, and what share of the queries carried no team tag. Those untagged queries are
unallocated spend, not free spend.

## Cost bases and FOCUS vocabulary

**Canonical.** The four bases are defined here and nowhere else. Other files apply them; when a rule
about what a figure *means* needs changing, it changes here and the others inherit it.

Four bases, never silently combined. FOCUS v1.4 column identifiers give them stable names:

| Basis | FOCUS column | Meaning here |
|---|---|---|
| Billed | `BilledCost` (M) | What the invoice charges. Needs Azure Cost Management |
| Effective | `EffectiveCost` (M) | Amortized, including commitment discounts |
| List | `ListCost` (M) | Usage × time-valid public price. What `list_prices` gives you |
| Contracted | `ContractedCost` (M) | Negotiated rate. Not derivable from `list_prices` |

`system.billing.list_prices` exposes `pricing.default` and `pricing.effective_list`. Effective list
resolves list plus promotional pricing. **Neither reflects negotiated discounts.** Treat Databricks
list cost and Azure billed cost as different measures — never invent a global discount factor to
convert one into the other.

**The two planes may not even share a currency.** One estate priced Databricks usage in USD while
Azure reported EUR, so the figures were never comparable as printed. State the currency beside every
figure, never sum across two, and do not apply an exchange rate the evidence did not supply — a
converted number is a modeled number and loses its measured label.

Where amortized cost equals actual cost, there is no commitment or reservation in play. That is a
finding, not a null result: it says the discount picture is empty rather than unavailable.

Attribution method carries its own FOCUS names: `AllocatedMethodId`, `AllocatedTags`, and
`AllocatedMethodDetails` (all conditional). Use them when stating how a shared cost was split.

## Evidence invariants

- Record source, query or export identifier, retrieval time, evidence period, currency, cost basis,
  and coverage for every figure.
- Join published prices on cloud, SKU, and validity interval. Real SKU names carry tier and region
  (`PREMIUM_ALL_PURPOSE_SERVERLESS_COMPUTE_US_EAST`), so match the region you are actually pricing.
  Left-join and report the unpriced remainder; an inner join hides it.
- Query every region relevant to an Azure price counterfactual.
- Classic compute cost is DBU plus VM plus material ancillary cost. Serverless SKUs bundle the VM —
  adding a VM line to a serverless workload double-counts it.
- **Per-workspace infrastructure is never bundled, however serverless the workload.** A workspace's
  managed resource group bills for its NAT gateway, public IPs and storage account whether or not
  anything runs. Measured in one estate: a workspace with zero DBUs for a week still cost €7.38,
  ninety percent of it NAT gateway — around €384 a year to exist. No Databricks system table shows
  a cent of it. Serverless closes the per-workload gap and never touches this one.
- Missing records prove nothing. Not zero cost, not zero use, not ownership.
- User assertions are valid business context and are not billing evidence.

## Freshness

Vendor facts drift: origins get renamed, tiers retire, functions move between billing origins. Those
carry a distillation date and a review date, so they live in `freshness.md` rather than here. Read it
during the preflight, before designing a query around a product's current behaviour.

## Fallbacks

Each plane degrades to a user-provided export, then to an explicitly limited estimate. When direct
access is missing, generate a targeted query or a precise export request — never install a
dependency, never create infrastructure, and never resize compute to make a query run.

**Billing is global; behaviour is regional.** `system.billing.usage` and `list_prices` cover the
whole account. `compute`, `lakeflow`, `query` and `access` carry only their own metastore's region,
and the workspace inventory is `system.access.workspaces_latest` — not a billing table.

A workload running outside your metastore's region therefore appears in the cost total with no
runtime detail behind it, and the gap is invisible unless you look for it: joining usage to
`system.lakeflow.jobs` simply returns no name. Report such a scope as cost without detail. Never
infer a cause you cannot observe, and never read the missing detail as missing cost.
