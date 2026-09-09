# Freshness

**Distilled 2026-07-01. Review by 2027-01-01.** Every item below is a vendor fact with a shelf life,
and this file exists so that shelf life is visible rather than buried in an evergreen reference.

A dated claim that survives its review date is not thereby confirmed — it is unreviewed. Re-check
against live `system.billing.list_prices` and current official documentation, then move the date.

**Rhythm: re-verify the price baseline every quarter, and before any client engagement.** The check
is one query — currently valid USD rows grouped by SKU family, compared against the table in
`opportunity-catalog.md` — and it takes minutes. Record the date of the check on that table whether
or not anything moved, because "unchanged" is a result and an untouched date is not.

Verified 2026-08-28: five of six sampled families matched exactly after five months. One floor was
wrong, and every range turned out to exclude one region. Drift is not the only way a baseline goes
wrong; a range that was never wide enough ages just as badly and looks healthier while doing it.

Verified 2026-09-09: every SKU stem named in `data-sources.md` was matched against
`system.billing.list_prices` and `system.billing.usage`. Twenty-one of twenty-two resolved. `GENIE`
existed in neither table under that name — the billed SKU is `GENIE_FREE_USAGE`, present in usage
from 2026-07-20 and absent from `list_prices` entirely. The model-serving vendor SKUs and the
networking egress families had both grown past what the table listed. A name that was never right
fails the same way as one that has drifted, and neither is visible without running the query.

Confirmed drift as of 2026-07-01. Treat every item as re-checkable, not settled:

- **"Serverless budget policies" are now "serverless usage policies."** The mechanism and the
  `budget_policy_id` column are unchanged; only the name moved.
- **DLT is now "Lakeflow Spark Declarative Pipelines" — in name only.** Billing is untouched:
  origin `DLT`, SKUs `DLT_CORE/PRO/ADVANCED_COMPUTE`. Do not rename anything in billing logic.
- **Monitoring's origin changed** to `DATA_QUALITY_MONITORING`.
- **`ai_query` bills under `MODEL_SERVING`**, not `AI_FUNCTIONS`.
- **Genie moved to pay-as-you-go on 2026-07-06** with its own metered DBUs, 150 free per identified
  user per month, and no free allowance for service principals. The SKU seen in
  `system.billing.usage` is `GENIE_FREE_USAGE`, not `GENIE`, and it has no `list_prices` row.
- **Lakebase snapshot storage became billable 2026-06-01.**
- **The Standard tier is being retired** — Azure auto-upgrades to Premium on 2026-10-01. Flag
  Standard-tier prices as sunsetting rather than quoting them as durable.
- **Governed tags went GA 2026-04-02.** Still Public Preview: serverless usage policies,
  `system.query.history`, query tags, Lakeflow pipeline tags, account budgets.
- Public pricing pages render figures in JavaScript, so static fetches cannot confirm `$/DBU`. Live
  `list_prices` is the only reliable price source.

## What to do when an item here is wrong

Correct it in place, move the review date, and say in the assessment that the correction was made —
a recommendation built on a renamed origin or a retired tier is wrong in a way the reader cannot
see. Live evidence and current official documentation outrank this file every time; it exists to
stop the skill assuming yesterday's product behaviour, not to be believed over a query.
