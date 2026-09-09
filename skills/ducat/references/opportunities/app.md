# Databricks App

_Opportunities for a Databricks App. Routed from `opportunity-catalog.md`, which carries the practice taxonomy and the price baseline every scope needs._

Practices: `usage-optimization`, `architecting-workload-placement`, `unit-economics`.

An app bills on **provisioned uptime, not work done**. Nothing about request volume appears in
billing, and there is no request-level access log — non-use is argued from behaviour and never
proven directly. Say so rather than implying the app is idle.

Two mechanisms that exist elsewhere do **not** apply, and proposing them wastes the reader's time:

- **No idle auto-stop.** An app bills every hour it is running. There is no inactivity timer to
  shorten, so the only way to stop paying is to stop the app.
- **Sizing is coarse.** Apps come in a small number of fixed sizes. Where the app already runs the
  smallest, downsizing is not an available lever — check before offering it.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Stop it outside a stated window | Flat DBU per hour across every hour, weekends indistinguishable from weekdays | Unavailable outside the window, and first access after a start waits on app startup — around a minute, not milliseconds |
| Size down | Current size against the size floor; sustained utilization if any is observable | Headroom at peak, if peak is even measurable |
| Retire it | Consumers observed over the period; the benefit its owner still claims | Whether anything depends on it — which billing cannot answer |

## The dependency that changes the arithmetic

An app usually has a backing store — a database instance, a warehouse, an endpoint — billing on its
own line. Assess them together or state plainly that you did not: the app's true cost of existing
includes what it keeps awake.

That phrasing is deliberate. **An app polling its dependency keeps that dependency from ever
idling.** One observed case: the app minted an authentication token roughly every three minutes,
around the clock, so its database never reached an idle state and a scale-to-zero timer could never
fire — at any timeout. The dependency's own idle-cost lever was worth **$0** until the app stopped
polling.

So where both are in scope, sequence matters and the saving is not the sum: stopping the app is
what makes the dependency's setting worth changing. Compute the target state with both applied,
per `proposal-contract.md`.

Where the backing store is a SQL warehouse, open `sql-warehouse.md` for its auto-stop and sizing
levers. Where it is a serving endpoint or a Lakebase instance, open `serving-or-vector-search.md`
for its scale-to-zero and sizing levers. Those two are the named second files, and nothing else in
either applies to an app assessment.

## Attribution

`usage_metadata.app_name` carries the app's name on every usage record, so attribution is **native**
and needs no tag, mapping or inference. The backing store is a separate object with its own
identifier — including it is a **manual** boundary decision by the requester, and is labelled as
such even when the connection is obvious.
