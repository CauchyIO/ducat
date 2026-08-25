# Freshness

**Distilled 2026-07-01. Review by 2027-01-01.** Every item below is a vendor fact with a shelf life,
and this file exists so that shelf life is visible rather than buried in an evergreen reference.

A dated claim that survives its review date is not thereby confirmed — it is unreviewed. Re-check
against live `system.billing.list_prices` and current official documentation, then move the date.

Confirmed drift as of 2026-07-01. Treat every item as re-checkable, not settled:

- **"Serverless budget policies" are now "serverless usage policies."** The mechanism and the
  `budget_policy_id` column are unchanged; only the name moved.
- **DLT is now "Lakeflow Spark Declarative Pipelines" — in name only.** Billing is untouched:
  origin `DLT`, SKUs `DLT_CORE/PRO/ADVANCED_COMPUTE`. Do not rename anything in billing logic.
- **Monitoring's origin changed** to `DATA_QUALITY_MONITORING`.
- **`ai_query` bills under `MODEL_SERVING`**, not `AI_FUNCTIONS`.
- **Genie moved to pay-as-you-go on 2026-07-06** with its own metered DBUs, 150 free per identified
  user per month, and no free allowance for service principals.
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
