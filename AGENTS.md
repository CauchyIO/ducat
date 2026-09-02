---
awow: anchored
anchor: git@github.com:CauchyIO/linear.git
project: databricks-cost-optimizer
---

# databricks-cost-optimizer

This repository is anchored to Cauchy's awow anchor at
[CauchyIO/linear](https://github.com/CauchyIO/linear). The anchor holds the team's board wiring,
conventions, style, and knowledge base; this repo holds only what is specific to the cost-optimizer
skill.

Work here is tracked on the **Cauchyio** Linear board (`CAU-` prefix,
[linear.app/cauchyio](https://linear.app/cauchyio)). The anchor is the single board, so nothing in
this repo needs to name it.

## Working here for the first time

Clone the anchor somewhere on your machine, then answer the one-time prompt that maps this repo to
it. The answer lands in `.awow/anchor.json`, which is machine-local and never committed — the
committed record is the `anchor:` line above.

## What this repo is

Read [`README.md`](README.md) for the skill's promise and boundaries, and
[`SKILL.md`](SKILL.md) for what it actually enforces. Both are authoritative; the boundaries in them
(read-only, one confirmed scope, Azure Databricks only, no implementation) are not conventions to be
softened.
