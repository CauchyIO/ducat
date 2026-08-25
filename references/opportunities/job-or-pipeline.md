# Job or pipeline

_Opportunities for a job or Lakeflow pipeline. Routed from `opportunity-catalog.md`, which carries the practice taxonomy and the price baseline every scope needs._

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
