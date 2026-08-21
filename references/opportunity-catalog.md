# Opportunity catalog

Optimization practices, routed to the confirmed scope. Load only the section matching the scope
type — the whole catalog is not meant to be in context at once.

Distilled 2026-08-21 from the Databricks cost component matrix, the Databricks cost tracking guide,
the 2026-07-01 pricing reassessment findings, and the FinOps Framework (see `NOTICE.md`).

## Contents

- [How to use this](#how-to-use-this)
- [Practice taxonomy](#practice-taxonomy)
- [Reference prices](#reference-prices)
- [Job or pipeline](#job-or-pipeline)
- [SQL warehouse](#sql-warehouse)
- [Serving or Vector Search](#serving-or-vector-search)
- [Team or workstream](#team-or-workstream)
- [Background platform service](#background-platform-service)

## How to use this

Every opportunity must trace to a practice below, to observed evidence, and to a reproducible
calculation. An item that cannot trace to all three is an observation, not a recommendation.

A generic ordering — remove waste, fix the schedule, rightsize, improve efficiency, change the
compute or pricing model, prevent recurrence — helps prioritize. It is not the source of truth. What
the evidence supports for this scope is.

Nothing here overrides live evidence or current official documentation. Prices and feature status
below carry an as-of date precisely because they expire.

## Practice taxonomy

The FinOps Framework, by the FinOps Foundation, used under CC BY 4.0. Distilled to identifiers,
titles, and URLs.

**Domains**

| Slug | Title |
|---|---|
| `understand-usage-cost` | [Understand Usage & Cost](https://www.finops.org/framework/domains/understand-usage-cost/) |
| `quantify-business-value` | [Quantify Business Value](https://www.finops.org/framework/domains/quantify-business-value/) |
| `optimize-usage-cost` | [Optimize Usage & Cost](https://www.finops.org/framework/domains/optimize-usage-cost/) |
| `manage-finops-practice` | [Manage the FinOps Practice](https://www.finops.org/framework/domains/manage-finops-practice/) |

**Capabilities**

| Slug | Title |
|---|---|
| `allocation` | [Allocation](https://www.finops.org/framework/capabilities/allocation/) |
| `anomaly-management` | [Anomaly Management](https://www.finops.org/framework/capabilities/anomaly-management/) |
| `architecting-workload-placement` | [Architecting & Workload Placement](https://www.finops.org/framework/capabilities/architecting-workload-placement/) |
| `automation-tools-services` | [Automation, Tools, & Services](https://www.finops.org/framework/capabilities/automation-tools-services/) |
| `budgeting` | [Budgeting](https://www.finops.org/framework/capabilities/budgeting/) |
| `data-ingestion` | [Data Ingestion](https://www.finops.org/framework/capabilities/data-ingestion/) |
| `executive-strategy-alignment` | [Executive Strategy Alignment](https://www.finops.org/framework/capabilities/executive-strategy-alignment/) |
| `finops-assessment` | [FinOps Assessment](https://www.finops.org/framework/capabilities/finops-assessment/) |
| `finops-education-enablement` | [FinOps Education & Enablement](https://www.finops.org/framework/capabilities/finops-education-enablement/) |
| `finops-practice-operations` | [FinOps Practice Operations](https://www.finops.org/framework/capabilities/finops-practice-operations/) |
| `forecasting` | [Forecasting](https://www.finops.org/framework/capabilities/forecasting/) |
| `governance-policy-risk` | [Governance, Policy & Risk](https://www.finops.org/framework/capabilities/governance-policy-risk/) |
| `intersecting-disciplines` | [Intersecting Disciplines](https://www.finops.org/framework/capabilities/intersecting-disciplines/) |
| `invoicing-chargeback` | [Invoicing & Chargeback](https://www.finops.org/framework/capabilities/invoicing-chargeback/) |
| `kpis-benchmarking` | [KPIs & Benchmarking](https://www.finops.org/framework/capabilities/kpis-benchmarking/) |
| `licensing-saas` | [Licensing & SaaS](https://www.finops.org/framework/capabilities/licensing-saas/) |
| `planning-estimating` | [Planning & Estimating](https://www.finops.org/framework/capabilities/planning-estimating/) |
| `rate-optimization` | [Rate Optimization](https://www.finops.org/framework/capabilities/rate-optimization/) |
| `reporting-analytics` | [Reporting & Analytics](https://www.finops.org/framework/capabilities/reporting-analytics/) |
| `sustainability` | [Sustainability](https://www.finops.org/framework/capabilities/sustainability/) |
| `unit-economics` | [Unit Economics](https://www.finops.org/framework/capabilities/unit-economics/) |
| `usage-optimization` | [Usage Optimization](https://www.finops.org/framework/capabilities/usage-optimization/) |

## Reference prices

**As of 2026-03-15, verified unchanged against live `list_prices` on 2026-07-01.** USD per DBU
unless noted, regional variants collapsed to ranges. This is a sanity-check baseline, not a quotable
price — query `system.billing.list_prices` for the account, region, and period you are assessing,
and use that. A figure here that disagrees with a live query loses.

| SKU | Tier | Price | Note |
|---|---|---|---|
| `ALL_PURPOSE_COMPUTE` (± Photon) | Premium | 0.55 | Standard 0.40, sunsetting |
| `ALL_PURPOSE_SERVERLESS_COMPUTE` | Premium | 0.95–1.14 | VM included |
| `JOBS_COMPUTE` (± Photon) | Premium | 0.30 | Standard 0.15, sunsetting |
| `JOBS_LIGHT_COMPUTE` | Premium | 0.22 | Legacy tier |
| `JOBS_SERVERLESS_COMPUTE` | Premium | 0.45–0.65 | VM included |
| `SQL_COMPUTE` | — | 0.22 | Flat across regions |
| `SQL_PRO_COMPUTE` | Premium | 0.55–0.96 | Regional |
| `SERVERLESS_SQL_COMPUTE` | Premium | 0.55–1.09 | Regional |
| `DLT_CORE / PRO / ADVANCED_COMPUTE` | — | 0.30 / 0.38 / 0.54 | Tier-based, not regional |
| `SERVERLESS_REAL_TIME_INFERENCE` | — | 0.07–0.12 | Regional |
| `ANTHROPIC / OPENAI / GEMINI_MODEL_SERVING` | — | 0.105 / 0.07 / 0.07 | Foundation model pricing is now published per 1M tokens; re-derive before quoting |
| `MODEL_TRAINING` | — | 0.65–1.11 | Regional |
| `DATABASE_SERVERLESS_COMPUTE` | — | 0.26–0.45 effective | ~50% promotional; expect change at GA |
| `DATABRICKS_STORAGE` | — | 0.023–0.041 per DSU | |
| Egress | — | 0.01–0.18 per GB | By route; inter-region 0.02–0.16 |
| `CLEAN_ROOMS_COLLABORATOR` | — | 50.00 per DAY | Flat daily, not a DBU rate |

Ratios that survive price drift better than the figures do, and that usually drive the decision:

1. **Job compute costs roughly 45% less than all-purpose** (0.30 vs 0.55 Premium). Usually the
   largest single lever on a job.
2. **Serverless carries a premium but bundles the VM.** Comparing a serverless DBU rate against a
   classic DBU rate without adding the classic VM cost is not a comparison.
3. **DLT is tier-based, not regional.** Core → Advanced is a 1.8× step.
4. **SQL classic is flat, Pro is regional.** Region choice matters for Pro and serverless, not for
   classic.
5. **Egress is easy to miss** and compounds with Delta Sharing and cross-region replication.

## Job or pipeline

Practices: `usage-optimization`, `architecting-workload-placement`, `rate-optimization`,
`allocation`, `governance-policy-risk`.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Move off all-purpose onto job compute | Job runs on an `ALL_PURPOSE` origin; ~45% rate gap | Loses interactive attach; cluster start latency per run |
| Rightsize the cluster | Utilization from `system.compute.*`, autoscale floor never reached, worker count vs runtime curve | Longer runtime; headroom against input growth must be stated |
| Fix autoscaling bounds | Min workers pinned high, or scale events clustered at the ceiling | Latency at the new floor |
| Change the schedule | Deadline headroom from downstream consumers; overlap with other work on shared capacity | Deadline risk; the input growth at which headroom disappears |
| Classic ↔ serverless | Full classic cost (DBU + VM + ancillary) against the serverless rate | Serverless removes VM control and pool reuse; tag mechanism changes to usage policies |
| Photon on or off | Runtime and DBU change together — Photon carries no separate SKU premium on jobs | Only worth it where the runtime reduction exceeds the DBU increase |
| Remediate failed and repaired runs | Cost by `result_state`; repair-run cost over 30 days; runs above the P90 baseline | None, usually — this is waste, not a service-level trade |
| Tier down DLT | `dlt_tier` in use vs features actually used (CDC, expectations, flow lineage) | Losing a tier feature the pipeline depends on |
| Cut idle time | Auto-termination settings; time between last command and termination | Restart latency for interactive users |

Attribution note that constrains everything above: **a job on all-purpose compute has no `job_id` on
its billing record.** Per-job cost on shared all-purpose compute cannot be measured, only modeled.
Say which one you did.

Normalize by cost per successful run when volume moved during the period. A pipeline that got
cheaper per run while total cost rose has not regressed.

## SQL warehouse

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

## Serving or Vector Search

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

## Team or workstream

Practices: `allocation`, `invoicing-chargeback`, `reporting-analytics`, `governance-policy-risk`.

A team is not a platform object. Build the mapping to objects that are, then keep the populations
separate — native, manual, inferred, unallocated — through to the output. A single allocated total
is what invites the dispute you were asked to settle.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Idle all-purpose compute | Clusters running without commands; auto-termination absent or long | Interactive convenience |
| Warehouse auto-stop and sizing | As in the warehouse section, scoped to the team's warehouses | Shared warehouses need proportional splitting first |
| Consolidate duplicated compute | Multiple clusters or warehouses with the same purpose and low utilization | Team autonomy; migration effort |
| Enforce tagging and usage policies | Unallocated share; tag coverage over time | **Not a saving.** It is a prerequisite that improves future attribution — say so explicitly |
| Move chargeback to the defensible portion | The native and manual populations, with the inferred and unallocated shown beside them | Charging back less than the true figure until attribution improves |

Deliver the allocation map itself. It is reusable as the team's showback definition and is often
worth more than the savings figure.

## Background platform service

Practices: `usage-optimization`, `governance-policy-risk`, `unit-economics`.

Predictive Optimization, Data Quality Monitoring, Data Classification, Fine-Grained Access Control,
Base Environments, AI Runtime. These bill through another service's SKU, are mostly not taggable,
and are found by filtering on `billing_origin_product` — never by SKU.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Narrow the enablement scope | Cost by catalog or schema against tables actually queried | Losing optimization or monitoring where it was earning its cost |
| Reduce monitor frequency | Refresh cost against how often results are read | Staleness in a governance signal |
| Disable where the benefit is unobserved | Cost of the service against measured benefit — query improvement, issues caught | The benefit may be real and unmeasured; say which |

The honest question for this scope is whether the service still earns its cost. Often it does, and
the finding is a narrowed scope rather than a removal. A background service is also the one place
where "we did not know we were paying for this" is a legitimate finding on its own.
