# Opportunity catalog

What every scope needs — the practice taxonomy and the price baseline — plus the route to the one
scope file that applies. The scope files live in `opportunities/`; load only the one you are
routed to, and any further file that one names.

Distilled 2026-08-21 from the Databricks cost component matrix, the Databricks cost tracking guide,
the 2026-07-01 pricing reassessment findings, and the FinOps Framework (see `NOTICE.md`).
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

**As of 2026-03-15, re-verified against live `list_prices` on 2026-08-28.** USD per DBU unless
noted, regional variants collapsed to ranges. This is a sanity-check baseline, not a quotable price
— query `system.billing.list_prices` for the account, region, and period you are assessing, and use
that. A figure here that disagrees with a live query loses.

**Ranges exclude India West (Jio),** where every SKU family runs two to three times the ceiling
below and where the two "flat" claims in this section do not hold. A live price above a range here
is a prompt to check the region before doubting the query.

| SKU | Tier | Price | Note |
|---|---|---|---|
| `ALL_PURPOSE_COMPUTE` (± Photon) | Premium | 0.55 | Standard 0.40, sunsetting |
| `ALL_PURPOSE_SERVERLESS_COMPUTE` | Premium | 0.95–1.14 | VM included |
| `JOBS_COMPUTE` (± Photon) | Premium | 0.30 | Standard 0.15, sunsetting |
| `JOBS_LIGHT_COMPUTE` | Premium | 0.22 | Legacy tier |
| `JOBS_SERVERLESS_COMPUTE` | Premium | 0.45–0.65 | VM included |
| `SQL_COMPUTE` | — | 0.22 | Flat across regions; India West 0.72 |
| `SQL_PRO_COMPUTE` | Premium | 0.55–0.96 | Regional |
| `SERVERLESS_SQL_COMPUTE` | Premium | 0.55–1.09 | Regional |
| `DLT_CORE / PRO / ADVANCED_COMPUTE` | — | 0.30 / 0.38 / 0.54 | Tier-based, not regional; India West 0.97 / — / 1.75 |
| `SERVERLESS_REAL_TIME_INFERENCE` | — | 0.07–0.12 | Regional |
| `ANTHROPIC / OPENAI / GEMINI_MODEL_SERVING` | — | 0.105 / 0.07 / 0.07 per DBU | Serving bills per DBU, never per token — pay-per-token endpoints are a separate SKU family. Verified against live `list_prices` 2026-09-03 |
| `MODEL_TRAINING` | — | 0.40–1.11 | Regional; floor corrected 2026-08-28 |
| `DATABASE_SERVERLESS_COMPUTE` | — | 0.26–0.45 effective | ~50% promotional; expect change at GA |
| `DATABRICKS_STORAGE` | — | 0.023–0.041 per DSU | |
| Egress | — | 0.01–0.18 per GB | By route; inter-region 0.02–0.16 |
| `CLEAN_ROOMS_COLLABORATOR` | — | 50.00 per DAY | Flat daily, not a DBU rate |

Ratios that survive price drift better than the figures do, and that usually drive the decision:

1. **Job compute costs roughly 45% less than all-purpose** (0.30 vs 0.55 Premium). Usually the
   largest single lever on a job.
2. **Serverless carries a premium but bundles the VM.** Comparing a serverless DBU rate against a
   classic DBU rate without adding the classic VM cost is not a comparison.
3. **DLT is tier-based, not regional.** Core → Advanced is a 1.8× step. India West is the one
   exception, and it is an exception to every ratio here.
4. **SQL classic is flat, Pro is regional.** Region choice matters for Pro and serverless, not for
   classic — again outside India West.
5. **Egress is easy to miss** and compounds with Delta Sharing and cross-region replication.

## Scope routing

Read exactly one, chosen by the confirmed scope. Reading a second means the scope was not confirmed.

| Confirmed scope | Read |
|---|---|
| A job or Lakeflow pipeline | `opportunities/job-or-pipeline.md` |
| A SQL warehouse | `opportunities/sql-warehouse.md` |
| A serving endpoint or Vector Search index | `opportunities/serving-or-vector-search.md` |
| A team or workstream | `opportunities/team-or-workstream.md` | 
| A background platform service | `opportunities/background-service.md` |
| A Databricks App | `opportunities/app.md` |

**The one exception is a dependency the chosen file names.** A scope file may tell you that
another object has to be accounted for and name the file covering it — only where that object
bills on its own line. Open each file it names, and take from each only the levers it was named
for, not its framing, its attribution rules, or its other opportunities. The permission does not
chain: a file named by that second file was not named by the first. Say in the proposal which
files were opened and why.

**A scope that matches none of these is not a licence to improvise.** Do not ask the user which
practice lens to apply — routing is this skill's job, and the question arrives at the worst moment,
after a baseline has been agreed. Instead: pick the file whose billing shape matches, say which and
why, re-verify every mechanism against current documentation rather than transferring it, and record
in the proposal both the substitution and any mechanism that did not transfer. Then file the gap so
the next assessment does not repeat the improvisation.

Billing shape is the criterion, not product family. Anything charging for provisioned uptime rather
than work done reads closest to `app.md` or `serving-or-vector-search.md`; anything charging per run
reads closest to `job-or-pipeline.md`.
