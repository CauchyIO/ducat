# Project profile — databricks-cost-optimizer

This repo is a read-only agent skill that establishes what one confirmed Azure Databricks scope — a
job, pipeline, SQL warehouse, serving endpoint, team, or workstream — costs today, then designs a
way to make it cost less. The audience is the engineer or finance partner who has to defend a
number: every proposed change carries the evidence behind it, the saving, the cost to make it, what
it gives up, and how to confirm afterwards that the saving landed.

The skill never writes to a Databricks workspace and never optimises an estate at once. Where
evidence is missing it narrows what it claims rather than guessing. The deliverable is a Markdown
proposal a human decides on.

**Stack.** A Markdown skill package — `SKILL.md` plus `references/` are the authoritative surface,
`docs/` covers operator setup, and `tools/check-package.py` (Python) validates the package. Evidence
comes from Databricks system tables, read through a read-only `databricks-sql` MCP server and the
Databricks CLI.
