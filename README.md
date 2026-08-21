# databricks-cost-optimizer

A read-only agent skill that works out what a specific Azure Databricks workload costs today, then
designs a way to make it cost less.

You point it at one thing — a job, a pipeline, a SQL warehouse, a team's workload — and it reads
your usage and billing data to establish what that thing actually costs. It then proposes concrete
changes. Each one comes with the evidence behind it, what you save, what the change costs to make,
what you give up, and how to confirm afterwards that the saving landed.

Two things it will not do. It never optimises an estate at once — every assessment starts from one
confirmed scope. And it never quotes a number it cannot support: where evidence is missing it says
so and narrows what it claims rather than guessing.

It never writes. No create, update, start, stop, resize or delete operation is invoked. The output
is a Markdown proposal a human reviews and decides on.

## Status

**Design complete, implementation not started.** [`docs/skill-spec.md`](docs/skill-spec.md) is the
design of record — what the skill does, what evidence it may use, and what it may claim.

The skill package itself is not yet written:

| Path | State |
|---|---|
| `SKILL.md` | Not written — scope gate, workflow, authorization boundary, routing |
| `references/data-sources.md` | Not written — evidence semantics, precedence, attribution, pricing joins |
| `references/opportunity-catalog.md` | Not written — optimization practices, routed by scope |
| `references/proposal-contract.md` | Not written — calculation contract, decision card, artifact structure |

Section 5 of the spec specifies the layout these will take and the sections each derives from.

## Install

Not yet installable.

## Invoke

Once packaged: explicitly as `$databricks-cost-optimizer`, or through automatic discovery when a
request matches the skill's description.

## Layout

```text
databricks-cost-optimizer/
├── SKILL.md
├── references/
│   ├── data-sources.md
│   ├── opportunity-catalog.md
│   └── proposal-contract.md
├── docs/
│   └── skill-spec.md
├── README.md
└── LICENSE
```

## Licence

MIT — see [LICENSE](LICENSE).
