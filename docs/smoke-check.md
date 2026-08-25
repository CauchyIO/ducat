# Smoke check: prove the evidence path

One job, one week, two independent sources that must agree. The cheapest end-to-end proof that the
credential, the warehouse, the transport and the system tables all work together.

Do not move on until every box is crossed. A half-passed smoke check is worse than none, because
every later figure inherits the doubt without carrying the warning.

| # | Confirm | Crossed when | Where |
|---|---|---|---|
| 1 | The schemas carry rows | All five sources return a count above zero, with a recent `latest` | [Does the evidence exist](#first-does-the-evidence-exist-at-all) |
| 2 | One job is chosen as the subject | It ran at least twice inside the window, so a rate can be compared across runs | [Cost from billing](#1-cost-from-billing) |
| 3 | Its cost is priced from billing | The query returns usage rows joined to a date-valid price | [Cost from billing](#1-cost-from-billing) |
| 4 | Its runs are listed independently | The timeline returns runs for the same job and window | [Runs from the timeline](#2-runs-from-the-timeline) |
| 5 | The two agree | DBU per hour holds constant across billed runs | [What agreement looks like](#what-agreement-looks-like) |
| 6 | Every mismatch has a named cause | Each unmatched run traces to lag, a window boundary, or a region | [Appears to fail](#two-ways-it-appears-to-fail-when-nothing-is-wrong) · [Genuinely fails](#when-it-genuinely-fails) |

Box 5 is the one that matters. Matching totals can agree by coincidence; a stable rate cannot.

## First: does the evidence exist at all?

Before reconciling anything, confirm the schemas carry rows. One query covers all five:

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
FROM system.access.workspaces_latest;
```

Five rows with a count above zero is the pass. Read `latest` as carefully as the count: a figure
several days old means the feed has stalled, not that the schema is off.

Zero on `query.history` is often genuine — nobody ran SQL on a warehouse in the window — so widen to
90 days before treating it as a gap. Zero on `billing.usage` never is, and means the schema is
enabled but not yet backfilled; check again in a few hours.

Databricks enables these schemas centrally. If one is genuinely empty the escalation is Databricks,
not a local admin, because the customer-facing enable API refuses them.

The two queries below are the reconciliation, and they come later — after a scope exists to point
them at.

## 1. Cost from billing

Pick a job that ran **at least twice** in the window. One run cannot show a constant rate, and a
constant rate is what box 5 tests.

```sql
SELECT u.usage_date, u.sku_name, round(u.usage_quantity, 4) AS quantity,
       round(u.usage_quantity * p.pricing.default, 4) AS list_cost_usd,
       u.usage_start_time, u.usage_end_time
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices p
  ON u.cloud = p.cloud AND u.sku_name = p.sku_name AND u.usage_unit = p.usage_unit
 AND u.usage_end_time >= p.price_start_time
 AND (u.usage_end_time <= p.price_end_time OR p.price_end_time IS NULL)
WHERE u.usage_metadata.job_id = '<job-id>' AND u.usage_date > current_date() - 7
ORDER BY u.usage_start_time
```

## 2. Runs from the timeline

```sql
SELECT run_id, min(period_start_time) AS started, max(period_end_time) AS ended,
       max(result_state) AS result_state
FROM system.lakeflow.job_run_timeline
WHERE job_id = '<job-id>' AND period_start_time > current_timestamp() - INTERVAL 8 DAYS
GROUP BY run_id ORDER BY started
```

## What agreement looks like

Every billed usage row falls inside a run window, and **DBU per hour is constant across runs**. The
constant rate is the real check — matching totals can agree by luck, a stable rate cannot. Billing
buckets are hourly, so one run straddling an hour boundary produces two usage rows.

## Two ways it appears to fail when nothing is wrong

**Billing lag.** A run that finished minutes ago has no usage row yet. Any statement about current
cost must say how fresh the billing data is.

**Window mismatch.** `usage_date > current_date() - 7` starts at midnight; `current_timestamp() -
INTERVAL 7 DAYS` starts at this time of day. The two disagree by up to a day, and the missing run
looks like missing cost. State the window, and use the same one on both sides.

## When it genuinely fails

A job with cost but no run record is not a bug — `system.billing.usage` is global while
`lakeflow`, `compute` and `query` are regional. A job running outside your metastore's region bills
here and is invisible here. Report that scope as cost-without-detail rather than guessing.
