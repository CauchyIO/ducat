# Contributing

Two checks run on this repository. The first exists because both failures it prevents
have already happened here.

## What runs

`tools/check-package.py` refuses two things.

**Credentials, in every file.** A service principal secret reached GitHub on 24 August 2026
inside a file swept up by `git add -A`. The fix was rotation, because deleting a pushed
secret does not unpublish it.

**Estate identifiers, in the package a client reads** — [`SKILL.md`](SKILL.md), `references/`, `docs/`
and the configuration beside them. A workspace id in a working note is nobody's problem.
The same id in a runbook is what a client sees, and the runbooks are clean today only
because someone grepped them by hand.

Identifiers are matched by shape, never by value. A checker holding the list of ids it
forbids would be the leak it exists to prevent, and would protect exactly one estate.

`tools/check-consistency.py` catches the quieter failure: an expired review date, a stale
price baseline, a scope file the routing table does not name, or a link that no longer
resolves. None of those produce a symptom. Each yields a clean run and a wrong assessment.

## When it runs

**Before the commit**, as a [pre-commit](https://pre-commit.com/) hook. Set it up once per
clone:

```sh
uv sync
uv run pre-commit install
```

If the clone was set up before September 2026 with `git config core.hooksPath .githooks`,
unset that first. `pre-commit install` refuses to run while it is set.

This is the one that matters. CI reports a credential faster; the hook is what stops it
reaching the remote at all. The same hook runs the consistency checker on staged markdown,
and ruff and mypy on staged Python, so a commit that would fail CI fails here first.

**In CI**, on every push and pull request, as the backstop for a machine where the hook was
never installed. One workflow runs the whole hook set over every tracked file — the same
`.pre-commit-config.yaml` the hook reads, so the two cannot check different things; a second
runs the test suite under `tests/`.

Run everything by hand any time:

```sh
uv run pre-commit run --all-files
```

## When it fails

The output names the file, the line and the rule.

- **A credential must be rotated**, not merely deleted. It is already on this machine and
  may be in the history.
- **An estate identifier belongs in `environment.local.md`**, which is gitignored, with a
  placeholder such as `<workspace-id>` where it was.
- **A deliberate example** needs `check-allow` on the line, and a sentence nearby saying why
  the example is safe to publish.

## Working on the scripts

Everything runs through [uv](https://docs.astral.sh/uv/): the scripts themselves, and the
formatter, linter, type checker and test runner pinned in `pyproject.toml` and `uv.lock`.

```sh
uv sync
uv run pre-commit run --all-files
uv run pytest
```

`pyproject.toml` is configuration, not a package. It has no build system and nothing in
it is installed except the tools. The scripts import only the standard library; `uv run`
is the one way to invoke them, from the hook, from CI and by hand.

## Still open

The checker knows the credential shapes this project actually handles — Databricks tokens
and OAuth secrets, private keys, JSON web tokens, and anything assigned to a
secret-looking name. It is not a general secret scanner. GitHub's own push protection is
the broad net, free on public repositories and licensed on private ones; whether it covers
this repository has not been settled.
