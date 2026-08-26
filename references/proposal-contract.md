# Proposal contract

What may be reported as a number, the shape every opportunity takes, and the structure of the final
artifact. Read this when quantifying opportunities and writing the handoff.

## Contents

- [Which figures may be reported](#which-figures-may-be-reported)
- [Savings calculation](#savings-calculation)
- [Which cost the figures are in](#which-cost-the-figures-are-in)
- [Portfolio, not a sum](#portfolio-not-a-sum)
- [Confidence](#confidence)
- [Decision card](#decision-card)
- [Final handoff](#final-handoff)

## Which figures may be reported

Gross saving, net saving, steady-state net rate, payback where material, a range or sensitivity
where a material input is uncertain, and a confidence level. Nothing else is reported as a number.

The restriction exists because every additional derived figure is another thing a reader can take
out of context into a budget conversation you will not be in.

## Savings calculation

Reproducible current-state versus target-state, stated for one analysis period `P` in months:

```text
gross saving(P)       = current platform cost(P) - target platform cost(P)          [currency]
net saving(P)         = gross saving(P)
                        - incremental operating cost(P)
                        - one-time change cost                                      [currency]
steady-state net rate = (gross saving(P) - incremental operating cost(P)) / P       [currency/month]
payback               = one-time change cost / steady-state net rate                [months]
```

Do not report payback when its inputs are merely directional, or when the steady-state net rate is
not positive. A payback figure computed from a guess reads as precision the evidence never had.

Compare like with like. Where volume moved between periods, normalize by a stable workload outcome —
successful runs, processed data, queries, served requests — and say which one.

Report a range or sensitivity whenever a material input is uncertain, and name the input.

## Which cost the figures are in

The four bases — billed, effective, list, contracted — are defined in `data-sources.md`, which is
canonical. What this file adds is which of them a *proposal* may lead with.

Billed or amortized cost is the primary basis when it is available, and the proposal states why that
basis fits the decision. Where it is not available, say so in the same breath as the figure rather
than in a footnote. Modeled cost — a counterfactual from measured inputs and stated assumptions — is
a separate plane again, and a target state is always modeled.

Carry the currency beside every figure and never sum across two. Both rules, and the reason a
converted number stops being a measured one, are in `data-sources.md`.

Classic compute cost includes DBUs, Azure VM cost, and material ancillary cost. Serverless SKUs
bundle the VM; adding a VM line to a serverless workload double-counts it. Storage, network,
serving, sync, and background service costs stay separate when material.

## Portfolio, not a sum

Individual opportunity values are shown for decision support. A selected portfolio total must
account for interactions and shared baselines.

Two changes that act on the same hours claim the same hours. Rightsizing a cluster and moving its
schedule both draw from one pool of idle time, so their combined saving is less than their sum —
often substantially. Compute the target state with all selected changes applied together, and
compare that against the single baseline. Where the naive sum differs materially, show both and
name the overlap; a reader who has seen the individual cards will otherwise assume you made an
arithmetic error.

## Confidence

| Level | Means |
|---|---|
| **Measured** | Directly supported by billed cost and observed workload evidence |
| **Modeled** | Calculated from measured usage and an explicit target-state counterfactual |
| **Directional** | Incomplete telemetry, attribution, or pricing prevents reliable quantification |

Confidence describes evidence quality, not enthusiasm. A large directional value does not outrank a
smaller measured one, and ordering a shortlist by value alone quietly implies it does — order by
value within a confidence level, or state the tie-break.

## Decision card

Every opportunity reaches the user in this shape. The shortlist is made of these; the handoff
aggregates the selected ones.

- identifier, title, confirmed scope;
- applicable practice and current authoritative source;
- observed evidence and baseline period;
- cost basis and operational driver;
- proposed change and the workload outcomes it protects;
- formula, assumptions, gross saving, change cost, ongoing cost, net saving, payback where material;
- confidence, sensitivity, risks, trade-offs, prerequisites;
- post-change measurement and success criteria;
- optional user-facing explanation.

A card missing the trade-off or the verification method is not ready to show. Those two fields are
what make it a decision rather than a suggestion.

## Final handoff

The only required engagement artifact is `cost-optimization-design.md`. Agree its location before
writing it, and treat that agreement as a decision rather than a formality.

**The deliverable describes one estate.** It names workspaces, objects, costs, sometimes people. It
belongs beside the evidence that produced it, on the machine that ran the assessment — not anywhere
it can be redistributed by an unrelated action.

So: never propose a git working tree, and never accept one without saying what it means. Before
writing, check whether the chosen path sits inside version control:

```sh
git -C "$(dirname <path>)" rev-parse --is-inside-work-tree 2>/dev/null
```

If that returns `true`, say so and offer an ignored directory or a path outside the repository. If
the user still wants it there, write it and tell them plainly that an assessment of their estate now
sits one `git add` from wherever that repository pushes. A secret reached a public remote in exactly
that way during this skill's own construction, through a sweeping add nobody inspected.

The same rule governs transcripts, exports and any scratch file holding query results.

1. **Decision summary** — confirmed scope and period, current cost and basis, selected
   opportunities, gross and net savings, payback, confidence, constraints, required decisions.
2. **Scope and evidence** — included and excluded objects, attribution map, unallocated spend,
   source coverage, timestamps, limitations.
3. **Current-state baseline** — cost components, operational drivers, reliability and utilization
   measures, Databricks-to-Azure reconciliation where available.
4. **Opportunity disposition** — selected, deferred, and rejected, each with a reason, and how
   overlapping savings were treated.
5. **Target-state design** — proposed configuration or operating-model changes, affected resources,
   dependencies, risks, trade-offs, prerequisites, and exact implementation steps, unexecuted.
6. **Financial case** — formulas, assumptions, gross saving, change and ongoing cost, net saving,
   sensitivity, with actual, list-price, and modeled values clearly separated.
7. **Implementation and verification** — sequencing, suggested ownership, acceptance criteria,
   post-change measurement period, validation queries, rollback or reconsideration conditions.
8. **Open decisions and limitations** — missing evidence, unresolved ownership, unsupported claims.

Section 7 is the one most often written thinly. A saving nobody can confirm 30 days later is
indistinguishable from a saving that never landed, so give the actual query and the number it should
return.

Add a calculation ledger only when the numbers cannot stay reproducible inside the document. Add
`scope.yaml` only when a multi-session engagement needs resumable state. Educational material is
included on request and must not obscure the decisions.
