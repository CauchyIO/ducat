# Smoke check: prove the evidence path

One job, one week, two independent sources that must agree. This is the cheapest end-to-end proof
that the credential, the warehouse, the MCP transport and the system tables all work — and the first
place the skill's own honesty rules get tested.

## 1. Cost from billing

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
