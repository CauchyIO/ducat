# Security policy

This skill reads usage and billing data from a real Azure Databricks estate and writes a
proposal that quotes it. Treat a vulnerability report with the same care as that data.

## Reporting a vulnerability

Do **not** open a public issue for a security problem. Use GitHub's private vulnerability
reporting on this repository's **Security** tab ("Report a vulnerability"). It is enabled.

Include the commit you tested against, a description of the problem, and the steps that
reproduce it. Expect an acknowledgement within a few business days.

## What matters here

The skill recommends reading only. It changes an estate only when the user asks for a named
change, and then makes only that change. A way to make it write without that request, to
make it change more than was named, or to make it act on an estate it was not scoped to, is
a vulnerability.

The sensitive assets are the outputs, not the code:

- **Proposals** carry real workspace, warehouse and job identifiers and real cost figures.
- **Session transcripts** can carry credentials in cleartext. One did.

Neither belongs in a repository. `tools/check-package.py` refuses a credential in any file
and an estate identifier in the package a client reads. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Supported versions

A tagged release is a snapshot and is not patched. Only the latest `main` receives
security fixes.
