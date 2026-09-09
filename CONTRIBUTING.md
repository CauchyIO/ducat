# Contributing

Two checks run on this repository. The first exists because both failures it prevents
have already happened here.

## What runs

`tools/check-package.py` refuses two things.

**Credentials, in every file.** A service principal secret reached GitHub on 24 August 2026
inside a file swept up by `git add -A`. The fix was rotation, because deleting a pushed
secret does not unpublish it.

**Estate identifiers, in the package a client reads** — [`skills/`](skills/), `docs/`, `hooks/`
and the configuration beside them. A workspace id in a working note is nobody's problem.
The same id in a runbook is what a client sees, and the runbooks are clean today only
because someone grepped them by hand.

Identifiers are matched by shape, never by value. A checker holding the list of ids it
forbids would be the leak it exists to prevent, and would protect exactly one estate.

`tools/check-consistency.py` catches the quieter failure: an expired review date, a stale
price baseline, a scope file the routing table does not name, or a link that no longer
resolves. It also refuses a reference file that has lost the dated sentence the first two
checks read, so rewording that sentence fails the run rather than silently ending the
checking. None of those produce a symptom. Each yields a clean run and a wrong assessment.

## When it runs

**Before the commit**, as a [pre-commit](https://pre-commit.com/) hook. Set it up once per
clone:

```sh
make install
make hooks
```

For anyone without `make`, that is `uv sync --locked` and then `uv run pre-commit install`.
`--locked` refuses to install from a lock that has drifted from `pyproject.toml`, rather
than quietly rewriting it; `uv lock` is the deliberate fix.

If the clone was set up before September 2026 with `git config core.hooksPath .githooks`,
unset that first. `pre-commit install` refuses to run while it is set.

This is the one that matters. CI reports a credential faster; the hook is what stops it
reaching the remote at all. The same hook runs the consistency checker on staged markdown,
and ruff and mypy on staged Python, so a commit that would fail CI fails here first.

**Weekly**, `tools/check-upstream.py` asks whether an upstream source the reference files were
distilled from has moved. Each source's published signal is pinned in that script — a content
commit id for a `learn.microsoft.com` article, a release tag for the FOCUS spec — and compared
against the live one. It is not a commit hook: it reaches the network, and committing must never
depend on a third party being reachable. A moved source opens a GitHub issue on this repository —
one issue, commented on thereafter, since a source stays moved until somebody re-distils it. A
source that cannot be read fails the run instead, so a network hiccup never masquerades as a
re-read somebody owes. Sources that publish no signal are named in the script as such, so their
absence stays visible.

**In CI**, on every push and pull request, as the backstop for a machine where the hook was
never installed. One workflow runs the whole hook set over every tracked file — the same
`.pre-commit-config.yaml` the hook reads, so the two cannot check different things; a second
runs the test suite under `tests/`.

Run everything by hand any time:

```sh
make check
```

That is the same `uv run --locked pre-commit run --all-files --show-diff-on-failure` that CI
runs, so a clean `make check` means a green check.

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
make install # uv sync --locked
make hooks   # uv run --locked pre-commit install
make check   # uv run --locked pre-commit run --all-files --show-diff-on-failure
make test    # uv run --locked pytest
make all     # check, then test
make clean   # remove the tool caches; keeps .venv
```

`make` on its own lists the targets and runs nothing.

`pyproject.toml` is configuration, not a package. It has no build system and nothing in
it is installed except the tools. The scripts import only the standard library; `uv run`
is the one way to invoke them, from the hook, from CI and by hand.

## Still open

The checker knows the credential shapes this project actually handles — Databricks tokens
and OAuth secrets, private keys, JSON web tokens, and anything assigned to a
secret-looking name. It is not a general secret scanner. GitHub's own push protection is
the broad net, free on public repositories and licensed on private ones; whether it covers
this repository has not been settled.
