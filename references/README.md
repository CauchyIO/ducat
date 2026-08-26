# References

These files are runtime instructions, not background reading. `SKILL.md` routes to them after the
scope is confirmed — `data-sources.md` during collection, `opportunity-catalog.md` once the scope
type is known, `proposal-contract.md` before anything is written down.

This is where the criteria live. A client who wants to change what the skill claims, or what counts
as a saving, changes something here. See `docs/README.md` for the design and setup documents.

| File | Governs | Read it when |
|---|---|---|
| `data-sources.md` | What counts as evidence, and what a figure means | A number is disputed, or attribution looks wrong |
| `freshness.md` | Vendor facts that drift, with a distillation date and a review date | Preflight, and whenever a product behaves unexpectedly |
| `opportunity-catalog.md` | The practice taxonomy, the price baseline, and the route to a scope | Deciding what to propose |
| `opportunities/` | One file per scope type — job, warehouse, serving, team, background service, app | After the scope is confirmed |
| `proposal-contract.md` | What may be reported, and how it is calculated | Writing or reviewing a proposal |

## The levers, file by file

**`data-sources.md`**

- **The precedence ladder.** Five rungs, live reads at the top, explicitly limited estimates at the
  bottom. A higher rung wins any disagreement. Reorder this and you change which source the skill
  believes.
- **The four cost bases** — billed, effective, list, contracted — which are never silently combined.
- **The attribution populations** — native, manual, inferred, unallocated — and the rule that
  unallocated cost stays visible rather than being redistributed. This is the lever most likely to
  be challenged, because it makes an uncomfortable number impossible to hide.
- **Query shape**: aggregation, row caps, and the currency and validity conditions that stop a join
  from silently doubling a cost.

**`opportunity-catalog.md`**

- **The practice taxonomy**, which every recommendation must trace back to.
- **The reference prices**, carried with an as-of date. They are a sanity check and lose to a live
  query. The ratios beneath them — job compute against all-purpose, for instance — survive price
  drift and usually decide the case.
- **The scope files** in `opportunities/` — job or pipeline, SQL warehouse, serving, team,
  background service, app — which determine what the skill even considers for a given target. One
  loads per assessment; adding an opportunity to the wrong file means it is never considered. The
  catalogue also states what to do for a scope type none of them covers.

**`proposal-contract.md`**

- **Which figures may be reported at all.** Gross saving, net saving, steady-state rate, payback
  where material, a range where an input is uncertain, and a confidence level. Nothing else is
  reported as a number, because every extra derived figure is one more thing a reader can carry into
  a budget conversation you are not in.
- **The savings formulas**, including when payback must be withheld.
- **The portfolio rule.** Overlapping changes claim the same hours, so a selected portfolio is
  computed together against one baseline rather than summed. Relax this and totals inflate.
- **The confidence levels** — measured, modeled, directional — and the rule that a large directional
  figure does not outrank a smaller measured one.
- **The decision card**, the shape of what a human signs off.

Changing a lever here changes what the skill will say. Record the change and the reason; these files
are the argument behind every figure it produces.
