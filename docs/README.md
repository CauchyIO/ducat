# Documentation

This guide covers all of the documentation located in the `docs/` directory. The `README.md` in the repository root covers the skill itself, what it does, and how to install it.

Two kinds of documents exist. `docs/` explains **how the skill was designed, how to set it up, and how to connect it**.
`references/`, at the repository root beside this folder, holds what the skill actually reads at runtime: the rules that decide what counts as evidence and what counts as a saving. Those are the rules a client is most likely to dispute. If you need to read or change them, see the last section of this document.

| File | What it is | Read it when |
|---|---|---|
| [`getting-started.md`](getting-started.md) | The setup sequence, in order, with what each step achieves | **Start here** if you are setting this up for the first time |
| [`create-read-only-principal.md`](create-read-only-principal.md) | Runbook for creating the read-only service principal the skill logs in with | Setting up a new workspace |
| [`connect-mcp-server.md`](connect-mcp-server.md) | Runbook for wiring the client to Databricks | After the principal exists |
| [`smoke-check.md`](smoke-check.md) | How to prove the evidence path returns defensible figures | After connecting, and whenever a number looks wrong |
| [`map-workspaces-to-azure.md`](map-workspaces-to-azure.md) | How to reach billed cost and the Azure resources a workspace consumes on its own | Only if list cost is not enough |
| [`personal-account-route.md`](personal-account-route.md) | The other route: the CLI as yourself, what it needs, what it cannot promise | When the service principal is unavailable, or you chose to read as yourself |

Session transcripts from validation runs are **not here and not committed**. A transcript records everything a run did, credentials in cleartext included, so transcripts stay in a gitignored `transcripts/` at the repository root. What those runs established travels in the Linear issue instead.

## What you can change, and where

**[`SKILL.md`](../SKILL.md) — the policy layer.** Nine invariants govern everything the skill will and will not do.
The consequential ones: scope is confirmed before any tool runs; a broad driver scan needs separate
confirmation and returns candidates rather than conclusions; cost bases are never blurred; a cheaper
design counts as a saving only when the workload's required outcomes survive; and the skill stops at
an approved design rather than implementing it. Loosening an invariant here and every downstream
document changes meaning.

**The setup runbooks — the access layer.** [`create-read-only-principal.md`](create-read-only-principal.md) and
[`connect-mcp-server.md`](connect-mcp-server.md) carry the decisions; [`smoke-check.md`](smoke-check.md) and [`map-workspaces-to-azure.md`](map-workspaces-to-azure.md) prove
and extend them. Each setup decision is a lever: how wide the read grant is
(catalog-level by default, which includes audit logs; a tighter per-schema grant needs an account
admin, and the runbook carries both), how long the
credential lives, which warehouse the queries run on, and whether the read-write tool stays denied
in the client configuration. The workspace-catalog exception is documented in the principal runbook
along with the reason it was left open.

## Where the analytical criteria live

If the question is *what counts as evidence* or *what counts as a saving*, the answer is in
`references/`, not here. That folder has its own guide at `references/README.md`, which enumerates
each lever in full. In short:

- **[`data-sources.md`](../references/data-sources.md)** — the evidence precedence ladder, the four cost bases, the attribution populations (native, manual, inferred, unallocated) and the rule that unallocated cost stays visible. Change these and you change what the skill is allowed to claim.
- **[`opportunity-catalog.md`](../references/opportunity-catalog.md)** and **`opportunities/`** — the practice taxonomy, a dated price baseline, and one file per scope type. The prices carry an as-of date and lose to a live query; the ratios beneath them survive price drift and usually decide the case.
- **[`proposal-contract.md`](../references/proposal-contract.md)** — which figures may be reported at all, how savings are calculated, the rule that overlapping opportunities are a portfolio rather than a sum, the confidence levels, and the shape of the decision card a human signs off.
