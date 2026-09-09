# SQL warehouse

_Opportunities for a SQL warehouse. Routed from `opportunity-catalog.md`, which carries the practice taxonomy and the price baseline every scope needs._

Practices: `usage-optimization`, `rate-optimization`, `allocation`, `reporting-analytics`.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Shorten auto-stop | Idle minutes between last query and stop, across the period | Cold-start latency on the next query |
| Resize the warehouse | Query duration distribution, queue time, spill, concurrency | Slower large queries; queueing at peak |
| Change tier (classic / pro / serverless) | Rate difference for the region against startup behaviour and feature use | Serverless removes control; pro is regionally priced |
| Align to a schedule | Query arrival by hour and weekday | Out-of-hours users hit a cold warehouse |
| Fix expensive queries | `system.query.history` by duration, bytes scanned, spill | Engineering time is the change cost |
| Allocate shared use proportionally | Execution time by `query_tags` team | Untagged queries stay unallocated, never spread silently |

Query tags exist only in `system.query.history`, only for SQL warehouse queries, and never in
billing usage. Any team split from them is a modeled allocation, not a measured cost.

Watch for AI functions billed through the warehouse context: `ai_query` surfaces under
`MODEL_SERVING`, and the other `ai_*` functions under `AI_FUNCTIONS`. Both can dominate a warehouse
line without appearing to be SQL cost.
