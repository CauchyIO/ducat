# Team or workstream

_Opportunities for a team or workstream. Routed from `opportunity-catalog.md`, which carries the practice taxonomy and the price baseline every scope needs._

Practices: `allocation`, `invoicing-chargeback`, `reporting-analytics`, `governance-policy-risk`.

A team is not a platform object. Build the mapping to objects that are, then keep the populations
separate — native, manual, inferred, unallocated — through to the output. A single allocated total
is what invites the dispute you were asked to settle.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Idle all-purpose compute | Clusters running without commands; auto-termination absent or long | Interactive convenience |
| Shorten warehouse auto-stop | Idle minutes between last query and stop, across the period, for each warehouse the team uses | Cold-start latency on the next query |
| Resize the team's warehouses | Query duration distribution, queue time, spill and concurrency, for those same warehouses | Slower large queries; queueing at peak |
| Consolidate duplicated compute | Multiple clusters or warehouses with the same purpose and low utilization | Team autonomy; migration effort |
| Move onto a shared warehouse | A warehouse of the same type in the same workspace, already running during the team's active hours | Contention at shared peaks; the team's cost loses its native `warehouse_id` attribution |
| Enforce tagging and usage policies | Unallocated share; tag coverage over time | **Not a saving.** It is a prerequisite that improves future attribution — say so explicitly |
| Move chargeback to the defensible portion | The native and manual populations, with the inferred and unallocated shown beside them | Charging back less than the true figure until attribution improves |

A warehouse that the team shares with another team has to be split before either lever above is
costed. Split it proportionally, by execution time from `query_tags`, and label the result a
modeled allocation rather than a measured cost. Queries carrying no tag stay unallocated, and are
never spread silently across teams.

**Look past the team's own warehouses.** A team's dedicated warehouse often idles between bursts
while another warehouse of the same type in the same workspace is already running. Find the
candidates in `system.compute.warehouses` by type and workspace, then set each candidate's billed
hours (`system.billing.usage` by `usage_metadata.warehouse_id` and hour) against the hours the team
queries (`system.query.history` by `start_time`). Hours where the candidate was already running cost
nothing extra; the rest it would have to run for. Size the move as a range. At best it saves the
team warehouse's whole cost, when every team hour falls inside the candidate's running hours; at
worst it saves that cost minus the candidate's extra hours at the candidate's rate. Widen the range
if the candidate would need a larger size to hold the team's queue time. Until
warehouse start and stop events are in the evidence, active hours come from billed hours and query
times, so say the overlap is approximated. After the move the team's cost no longer carries its own
`warehouse_id`, so chargeback rests on query tags: state that alongside the saving.

Deliver the allocation map itself. It is reusable as the team's showback definition and is often
worth more than the savings figure.
