# Writing the skill package

**Decision record — 2026-08-21.** The skill package was implemented from `docs/skill-spec.md`.

## What was written

| File | Lines | Carries |
|---|---|---|
| `SKILL.md` | 203 | Scope gate, workflow, invariants, claim gates, precedence, routing |
| `references/data-sources.md` | 231 | Core join, billing-origin-vs-SKU, attribution caveats, FOCUS cost bases, freshness overlay |
| `references/opportunity-catalog.md` | 214 | FinOps taxonomy, dated price baseline, five scope-routed practice sections |
| `references/proposal-contract.md` | 125 | Savings formulas, portfolio rule, confidence levels, decision card, handoff |

`README.md` and `NOTICE.md` were updated — both described these files as unwritten, and NOTICE
carried two "takes effect when the enumeration lands" clauses that now record the distillation date.

## Sources used

The four internal seeds named in §6.5 were located and confirmed before use. Paths below are
relative to `~/cauchy-projects/`, in sibling repositories that do not travel with this one — anyone
outside that machine will not find them, and §6.5 intends the seeds to stay uncommitted.

| Seed | File |
|---|---|
| FinOps agent prompts | `linear/integrations/finops_agent/prompts.py` |
| Cost component matrix | `linear/design/blogs/finops_databricks/cost_component_matrix.md` |
| Cost tracking guide | `linear/design/blogs/finops_databricks/draft.md` |
| Pricing reassessment findings | `linear/design/blogs/finops_databricks/pricing-reassessment-findings.md` |

The third-party enumerations were already distilled at `system_tables_os/reference/finops/` — same
caveat on the path — carrying FinOps Framework and FOCUS v1.4 with a retrieval date and FOCUS commit
matching `NOTICE.md`. No re-distillation and no web fetch were needed.

## Decisions

**Prices are carried with an as-of date.** The March-2026 table ships with the 2026-07-01
reassessment corrections applied, marked as a sanity-check baseline that loses to a live
`list_prices` query. A ratios list sits beneath it, because the ratios (job compute ~45% under
all-purpose) survive price drift and usually decide the case.

**The description is broader than the spec's §5 proposal.** The spec's sentence is kept, with
symptom-shaped phrasings added — someone whose pipeline got expensive rarely types "optimize."

**Skill files follow the 500-line convention, not the 500-word rule** in `CLAUDE.md`, which governs
human-facing documents. Skill files are runtime instructions.

**Freshness drift was folded into the references,** not left in the seeds: the monitoring origin
rename, `ai_query` billing under `MODEL_SERVING`, the usage-policy rename, Genie pay-as-you-go, and
the Standard-tier sunset.

## Open

The package is unvalidated. Section 10 of the spec fixes four behavioural witnesses.

- The reviewer tests the scope gate with an unscoped request.
- The reviewer tests the claim gates with Azure cost withheld.
- The reviewer tests portfolio maths with two overlapping opportunities.
- The reviewer tests the read-only boundary with an apply request.
- The author re-verifies every price before a client engagement.
