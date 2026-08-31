# Smoke check: prove the evidence path

One job, one week, two independent sources that must agree. The cheapest end-to-end proof that the
credential, the warehouse, the transport and the system tables all work together.

Five checks, in order. Do not move on until each one passes. A half-passed smoke check is worse than
none, because every later figure inherits the doubt without carrying the warning.

**This file is used twice, at two different points in the setup sequence.**

**Check 1 comes first, before anything else exists.** Run it as yourself, a workspace admin, in the
SQL editor or the CLI. It answers a question that has nothing to do with this skill: does this
workspace have system tables with rows in them? There is no point building an identity to read data
that is not there. This is step 1 of [`getting-started.md`](getting-started.md).

**Checks 2 to 5 come last**, once the principal, the warehouse and the connection all exist. Run
them *as the principal, through the MCP connection* — that combination is what is being tested, and
running them as yourself proves only that you can read. This is step 4 of `getting-started.md`.

## Check 1 — the schemas carry rows

*Run as yourself, before the principal exists.*

Before building anything, confirm there is anything to read. One query covers all five sources the
skill depends on.

```sql
SELECT 'billing.usage' AS source, count(*) AS row_count,
       cast(min(usage_date) AS string) AS earliest, cast(max(usage_date) AS string) AS latest
FROM system.billing.usage WHERE usage_date > current_date() - 30
UNION ALL
SELECT 'compute.clusters', count(*), cast(min(change_time) AS string), cast(max(change_time) AS string)
FROM system.compute.clusters
UNION ALL
SELECT 'lakeflow.jobs', count(*), cast(min(change_time) AS string), cast(max(change_time) AS string)
FROM system.lakeflow.jobs
UNION ALL
SELECT 'query.history', count(*), cast(min(start_time) AS string), cast(max(start_time) AS string)
FROM system.query.history WHERE start_time > current_timestamp() - INTERVAL 30 DAYS
UNION ALL
SELECT 'access.workspaces_latest', count(*), cast(min(create_time) AS string), cast(max(create_time) AS string)
FROM system.access.workspaces_latest
```

**Passes when** five rows come back, each with a count above zero and a `latest` within the last day
or two.

Read `latest` as carefully as the count. A figure several days old means the feed has stalled, not
that the schema is missing.

Zero on `query.history` is often genuine — nobody ran SQL on a warehouse in the window — so widen to
90 days before treating it as a gap. Zero on `billing.usage` never is: the schema is enabled but not
yet backfilled, so check again in a few hours.

Databricks enables these schemas centrally. If one is genuinely empty, the escalation is Databricks
rather than a local admin, because the customer-facing enable API refuses them.

## Check 2 — find a job that ran at least twice

*Checks 2 to 5 run as the principal, through the MCP connection.*

The reconciliation compares a *rate* across runs, so one run is not enough. This finds candidates.

```sql
SELECT job_id, count(DISTINCT run_id) AS runs,
       min(period_start_time) AS first_run, max(period_end_time) AS last_run
FROM system.lakeflow.job_run_timeline
WHERE period_start_time > current_timestamp() - INTERVAL 8 DAYS
GROUP BY job_id HAVING count(DISTINCT run_id) >= 2
ORDER BY runs DESC
```

**Passes when** at least one job comes back. Take its `job_id` into checks 3 and 4.

If nothing comes back, the workspace ran no job twice this week. Widen the window rather than
picking a single-run job — a rate you cannot compare tests nothing.

## Check 3 — price that job's cost from billing

The first of the two independent sources. Substitute the `job_id` from check 2.

```sql
SELECT u.usage_date, u.sku_name, round(u.usage_quantity, 4) AS quantity,
       round(u.usage_quantity * lp.pricing.effective_list.default, 4) AS list_cost_usd,
       u.usage_start_time, u.usage_end_time
FROM system.billing.usage u
JOIN system.billing.list_prices lp
  ON  lp.cloud         = u.cloud
  AND lp.sku_name      = u.sku_name
  AND lp.usage_unit    = u.usage_unit
  AND lp.currency_code = 'USD'
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_metadata.job_id = '<job-id>' AND u.usage_date > current_date() - 7
ORDER BY u.usage_start_time
```

**Passes when** every row carries a non-null `list_cost_usd`.

A null price means the join found no valid row for that SKU, unit and moment — the figure is
unpriced rather than free. The `currency_code` filter is not optional: without it a SKU published in
several currencies returns one row per currency and the cost multiplies silently.

## Check 4 — list the same job's runs from the timeline

The second source, which knows nothing about billing.

```sql
SELECT run_id, min(period_start_time) AS started, max(period_end_time) AS ended,
       max(result_state) AS result_state
FROM system.lakeflow.job_run_timeline
WHERE job_id = '<job-id>' AND period_start_time > current_timestamp() - INTERVAL 8 DAYS
GROUP BY run_id ORDER BY started
```

**Passes when** it returns the runs check 2 promised, with start and end times that bracket the
usage rows from check 3.

## Check 5 — the two sources agree

The one that matters. Matching totals can agree by coincidence; a stable rate cannot.

```sql
WITH runs AS (
  SELECT run_id, min(period_start_time) AS started, max(period_end_time) AS ended
  FROM system.lakeflow.job_run_timeline
  WHERE job_id = '<job-id>' AND period_start_time > current_timestamp() - INTERVAL 8 DAYS
  GROUP BY run_id
)
SELECT r.run_id, r.started,
       round(sum(u.usage_quantity), 4) AS dbus,
       round(timestampdiff(SECOND, r.started, r.ended) / 3600.0, 4) AS hours,
       round(sum(u.usage_quantity) / (timestampdiff(SECOND, r.started, r.ended) / 3600.0), 2) AS dbu_per_hour
FROM runs r
LEFT JOIN system.billing.usage u
  ON  u.usage_metadata.job_id = '<job-id>'
  AND u.usage_start_time < r.ended
  AND u.usage_end_time   > r.started
GROUP BY r.run_id, r.started, r.ended
ORDER BY r.started
```

**Passes when** `dbu_per_hour` is roughly constant across runs — same compute, same rate, whatever
the run lengths.

A run with null `dbus` had no billing row overlap. That is not automatically a failure; the two
sections below say when it is.

## When a mismatch is not a fault

**Billing lag.** A run that finished minutes ago has no usage row yet. Any statement about current
cost must say how fresh the billing data is.

**Window mismatch.** `usage_date > current_date() - 7` starts at midnight; `current_timestamp() -
INTERVAL 7 DAYS` starts at this time of day. The two disagree by up to a day, and the missing run
looks like missing cost. State the window, and use the same one on both sides.

## When it genuinely fails

A job with cost but no run record is not a bug. `system.billing.usage` is global while `lakeflow`,
`compute` and `query` are regional, so a job running outside your metastore's region bills here and
is invisible here.

Report that scope as cost-without-detail rather than guessing.
