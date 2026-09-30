# Job or pipeline

_Opportunities for a job or Lakeflow pipeline. Routed from `opportunity-catalog.md`, which carries the practice taxonomy and the price baseline every scope needs._

Practices: `usage-optimization`, `architecting-workload-placement`, `rate-optimization`,
`allocation`, `governance-policy-risk`.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Move off all-purpose onto job compute | Job runs on an `ALL_PURPOSE` origin; ~45% rate gap | Loses interactive attach; cluster start latency per run |
| Rightsize the cluster | Utilization from `system.compute.*`, autoscale floor never reached, worker count vs runtime curve; node size in cores and memory from `system.compute.node_types`, so the oversizing is stated in hardware | Longer runtime; headroom against input growth must be stated |
| Fix autoscaling bounds | Min workers pinned high, or scale events clustered at the ceiling | Latency at the new floor |
| Change the schedule | Deadline headroom from downstream consumers; overlap with other work on shared capacity | Deadline risk; the input growth at which headroom disappears |
| Classic ↔ serverless | Full classic cost (DBU + VM + ancillary) against the serverless rate | Serverless removes VM control and pool reuse; tag mechanism changes to usage policies |
| Photon on or off | Runtime and DBU change together — Photon carries no separate SKU premium on jobs | Only worth it where the runtime reduction exceeds the DBU increase |
| Remediate failed and repaired runs | Cost by `result_state` — from `system.lakeflow.job_run_timeline` for jobs, `system.lakeflow.pipeline_update_timeline` for pipelines; repair-run cost over 30 days; runs above the P90 baseline, and the task behind them from per-task runtimes in `system.lakeflow.job_task_run_timeline` | None, usually — this is waste, not a service-level trade |
| Tier down DLT | `dlt_tier` in use vs features actually used (CDC, expectations, flow lineage) | Losing a tier feature the pipeline depends on |
| Cut idle time | Auto-termination settings; time between last command and termination | Restart latency for interactive users |

Attribution note that constrains everything above: **a job on all-purpose compute has no `job_id` on
its billing record.** Per-job cost on shared all-purpose compute cannot be measured, only modeled.
Say which one you did. Find the cluster through `compute_ids` in
`system.lakeflow.job_task_run_timeline`; that identifies the compute, not the job's share of it.

**A job that only runs other jobs has no cost of its own.** Its tasks are `run_job_task`s that
start other jobs, so its billing records are empty and its task runs carry no `compute_ids`. The
cost sits on the jobs it runs, each under its own `job_id`; the orchestrator's cost is their sum.
Find them in `system.lakeflow.job_run_timeline`: each child run names the task run that started it
in `source_task_run_id`, which is a `run_id` in `system.lakeflow.job_task_run_timeline` under the
orchestrator's `job_id`. Join on that column, not on `trigger_type`: the documented `RUN_JOB_TASK`
value did not appear in a live workspace, where every child run read `ONETIME`. A pipeline it
starts names the job in `trigger_details.job_task` on `system.lakeflow.pipeline_update_timeline`.
These links exist only for runs from early December 2025; before that, confirm the list of jobs
with the user. An empty cost for a job is never read as all-purpose compute until its tasks have
been checked: empty `compute_ids` on a run-job task means it ran nothing itself.

Normalize by cost per successful run when volume moved during the period. A pipeline that got
cheaper per run while total cost rose has not regressed.
