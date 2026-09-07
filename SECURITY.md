# Security policy

This skill reads usage and billing data from a real Azure Databricks estate and writes a
proposal that quotes it. Treat a vulnerability report with the same care as that data.

## Reporting a vulnerability

Do **not** open a public issue for a security problem. Use GitHub's private vulnerability
reporting on this repository's **Security** tab ("Report a vulnerability"). It is enabled.

Include the commit you tested against, a description of the problem, and the steps that
reproduce it. Expect an acknowledgement within a few business days.

## What matters here

The skill is **read-only** by design. It never creates, updates, starts, stops, resizes or
deletes anything in an estate. A way to make it write, or to make it act on an estate it
was not scoped to, is a vulnerability.

The sensitive assets are the outputs, not the code:

- **Proposals** carry real workspace, warehouse and job identifiers and real cost figures.
- **Session transcripts** can carry credentials in cleartext. One did.

Neither belongs in a repository. `tools/check-package.py` refuses a credential in any file
and an estate identifier in the package a client reads. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Supported versions

There are no releases. Only the latest `main` receives security fixes.
