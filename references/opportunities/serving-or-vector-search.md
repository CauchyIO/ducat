# Serving or Vector Search

_Opportunities for a serving endpoint or Vector Search index. Routed from `opportunity-catalog.md`, which carries the practice taxonomy and the price baseline every scope needs._

Practices: `usage-optimization`, `architecting-workload-placement`, `unit-economics`.

Both bill in more than one component, which is where assessments usually go wrong.

- **Vector Search** bills endpoint serving on `SERVERLESS_REAL_TIME_INFERENCE` **and** index sync on
  `JOBS_SERVERLESS_COMPUTE`, both under origin `VECTOR_SEARCH`. An index synced continuously against
  an endpoint serving few queries spends most of its cost on maintenance nobody asked for.
- **Model serving** splits between custom inference and the foundation model SKUs. Foundation model
  pricing is published per 1M tokens; do not carry a flat per-DBU figure into a counterfactual.
- **Lakebase** bills compute, storage in DSUs, and background maintenance. Snapshot storage became
  billable 2026-06-01.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Continuous → triggered sync | Sync cost share; index update frequency against query volume | A stated freshness delay, confirmed with every consuming application |
| Scale-to-zero or right-size the endpoint | Request rate by hour; provisioned concurrency vs served requests | Cold-start latency on first request |
| Consolidate endpoints | Endpoints serving overlapping models or low traffic | Blast radius; noisy-neighbour latency |
| Change model tier | Cost per served request by model family | Quality change — needs an evaluation, not an assertion |
| Retire the workload | Consumers observed over the period; benefit claimed by the owner | Whether anything still depends on it |

Normalize by cost per served request. An endpoint whose cost rose with traffic is behaving
correctly; one whose cost rose without traffic is the finding.
