# Smoke check: prove the evidence path

This runbook proves that the skill can read what it needs to read. You take one job, look at one
week of its history, and ask two parts of Databricks about it: one that knows what it cost, one that
knows what it did. The two answers come from sources that know nothing about each other, so when the
answers agree you have shown that the credential, the warehouse, the connection, and the system
tables are all working together.

Work through the five checks in order and do not move on until a check passes. A smoke check that
half passed is worse than no smoke check at all, because every figure the skill later produces
inherits the doubt without carrying a warning about it.

**Note:** You will open this runbook twice — check 1 before you build anything, run as yourself, and
checks 2 to 5 after the connection exists, run as the principal.

**Check 1 comes first, before you have built anything.** Run check 1 as yourself, using a workspace
admin login, in the SQL editor or through the CLI. Check 1 asks a question about the workspace
rather than about the skill: do the system tables exist and do they contain data? Building an
identity to read tables that turn out to be empty wastes an hour. Check 1 is step 1 of
[`getting-started.md`](getting-started.md).

**Checks 2 to 5 come last,** once the service principal, the warehouse and the connection all
exist. Run those four checks as the principal, through the MCP connection, because the combination
of all four pieces is what you are testing. Running the same queries as yourself would prove only
that you can read the tables. Checks 2 to 5 are step 4 of [`getting-started.md`](getting-started.md).

Running a query through the MCP connection means asking Claude Code to run it. Start a session with
the plugin installed, in the shell where the two variables are exported, confirm with `/mcp` that
`databricks-sql` is connected, then paste the query and ask for it to be run. Claude sends the query to Databricks over the connection, waits
for the statement to finish, and shows the rows in the conversation. The query executes as the
service principal, because the token in the connection belongs to the principal rather than to you —
which is exactly why these four checks test the setup and not your own access.

Only reads will run this way. The plugin's hook denies the read-write tool, so a query that
tried to change anything would be refused before it reached Databricks. Every query below is a
`SELECT`, so the question never arises.

## Check 1 — the schemas carry rows

*Run this check as yourself, before the service principal exists.*

Confirm that the workspace holds data worth reading before you build anything to read it with. A
single query covers all five sources the skill depends on.

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

**Passes when** the query returns five rows, `billing.usage` carries a count above zero, and the
`latest` dates are recent.

Only `billing.usage` must contain rows. A workspace that bills anything at all produces billing
records, so a count of zero there means the schema has been switched on but has not finished
backfilling. Wait a few hours and run check 1 again.

The other four sources may legitimately be empty, and a count of zero tells you about the workspace
rather than about the setup. A workspace where nobody has created a job leaves `lakeflow.jobs`
empty. A workspace running only serverless compute leaves `compute.clusters` empty. A workspace
where nobody has run SQL on a warehouse this month leaves `query.history` empty — widen the window
to 90 days before drawing any conclusion from that one.

Read the `latest` dates as carefully as you read the counts. A date several days old means the feed
into that table has stalled, which matters more than a low count and is easy to miss.

Databricks switches these schemas on centrally, so if a schema is genuinely missing rather than
merely empty, raise the problem with Databricks rather than with a local administrator. The
customer-facing enable API refuses to touch them.

## Check 2 — find a job that ran at least twice

*Run checks 2 to 5 as the principal, through the MCP connection.*

Check 5 compares a rate across several runs of the same job, so a job that ran only once will not
serve. The query below lists the jobs that ran often enough to use.

```sql
SELECT job_id, count(DISTINCT run_id) AS runs,
       min(period_start_time) AS first_run, max(period_end_time) AS last_run
FROM system.lakeflow.job_run_timeline
WHERE period_start_time > current_timestamp() - INTERVAL 8 DAYS
GROUP BY job_id HAVING count(DISTINCT run_id) >= 2
ORDER BY runs DESC
```

**Passes when** the query returns at least one job. Carry that `job_id` into checks 3, 4 and 5.

If the query returns nothing, no job in this workspace ran twice during the past week. Widen the
window rather than settling for a job that ran once, because a rate you cannot compare against
anything tests nothing.

## Check 3 — price that job's cost from billing

This query is the first of the two independent sources. Substitute the `job_id` you took from
check 2.

```sql
SELECT u.usage_date, u.sku_name, round(u.usage_quantity, 4) AS quantity,
       round(u.usage_quantity * lp.pricing.effective_list.default, 4) AS list_cost_usd,
       u.usage_start_time, u.usage_end_time
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON  lp.cloud         = u.cloud
  AND lp.sku_name      = u.sku_name
  AND lp.usage_unit    = u.usage_unit
  AND lp.currency_code = 'USD'
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_metadata.job_id = '<job-id>' AND u.usage_date > current_date() - 7
ORDER BY u.usage_start_time
```

**Passes when** every row carries a `list_cost_usd` that is not null.

A null price means the join found no price row valid for that SKU, that unit and that moment, so
the usage is unpriced rather than free. The `LEFT JOIN` is what lets such a row appear at all —
under an inner join it would vanish and this check could never fail. Keep the `currency_code`
filter, and keep it in the `ON` clause: a SKU published in several currencies returns one row per
currency without it, and the cost silently multiplies.

## Check 4 — list the same job's runs from the timeline

This query is the second source. The run timeline records what the scheduler did and knows nothing
about what anything cost.

```sql
SELECT run_id, min(period_start_time) AS started, max(period_end_time) AS ended,
       max(result_state) AS result_state
FROM system.lakeflow.job_run_timeline
WHERE job_id = '<job-id>' AND period_start_time > current_timestamp() - INTERVAL 8 DAYS
GROUP BY run_id ORDER BY started
```

**Passes when** the query returns the runs that check 2 counted, and the start and end times
bracket the usage rows from check 3.

## Check 5 — the two sources agree

This is the check the other four exist to make possible. Two totals can match by coincidence, but
two sources rarely produce the same rate by accident.

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

**Passes when** `dbu_per_hour` stays roughly constant from run to run. The same compute charges the
same rate whatever the run lengths, so a stable rate means the billing rows and the run records are
describing the same work.

A run whose `dbus` is null had no billing row overlapping it. That is not automatically a failure —
the two sections below explain when a gap is expected and when a gap is a real problem.

## When a mismatch is not a fault

**Billing lags behind the work.** A run that finished minutes ago has no usage row yet. Whenever the
skill states a current cost, it also has to state how fresh the billing data behind that cost is.

**The two windows do not start at the same moment.** Check 3 uses `usage_date > current_date() - 7`,
which begins at midnight; checks 2, 4 and 5 use `current_timestamp() - INTERVAL 8 DAYS`, which begins
at whatever time of day you run them. The extra day on the timeline side absorbs that offset, so a
run near the edge of the billing window still has a run record to match against. A run outside both
windows looks like missing cost and is not. State the window you used, and use the same one on both
sides of any comparison you report.

## When the tables cannot explain the cost

A job that has cost but no run record is not a bug in the setup. `system.billing.usage` covers the
whole account, while `lakeflow`, `compute` and `query` only cover your metastore's region. A job
running in another region therefore bills into the tables you can see and leaves no trace in the
tables that would explain it.

When that happens, report the scope as cost without detail rather than guessing at what produced
the cost.
