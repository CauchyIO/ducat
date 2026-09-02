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
| Enforce tagging and usage policies | Unallocated share; tag coverage over time | **Not a saving.** It is a prerequisite that improves future attribution — say so explicitly |
| Move chargeback to the defensible portion | The native and manual populations, with the inferred and unallocated shown beside them | Charging back less than the true figure until attribution improves |

A warehouse that the team shares with another team has to be split before either lever above is
costed. Split it proportionally, by execution time from `query_tags`, and label the result a
modeled allocation rather than a measured cost. Queries carrying no tag stay unallocated, and are
never spread silently across teams.

Deliver the allocation map itself. It is reusable as the team's showback definition and is often
worth more than the savings figure.
