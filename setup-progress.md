# awow setup progress

install-shape: anchored
anchor: git@github.com:CauchyIO/linear.git
project: databricks-cost-optimizer
track: team
hat: both
route: guided
boards: cauchyio
teams: Cauchyio
board-url: https://linear.app/cauchyio
surface: mcp
board-mcp: linear-server (confirmed 2026-09-02, via the anchor's context/tooling/board.md)
harness: Claude Code

## Required core

- [x] 0. Installer — n/a (plugin install; no vendored tree)
- [x] Anchored registration — done-by: pvizan
  - Anchor identified and origin-matched against a local checkout.
  - Machine link written to the gitignored `.awow/anchor.json` (never committed).
  - Anchored-repo PR: `AGENTS.md` connector, project-scope plugin enable, `context/mission.md`,
    `.awow/` gitignore entry.
  - Anchor PR: stands up `context/knowledge-sources/` (the anchor had no catalog) with this repo's
    OKF record and index entry.
- [x] 1. Board — inherited from the anchor. The anchor's `context/tooling/board.md` specifies the
      single Cauchyio Linear board; this repo adds no board spec of its own.
  - `context/board-scope.md` deliberately skipped: one board, nothing to disambiguate.

## Deferred fills

None landed. Each fills on first need, from the anchor where the anchor already answers it:
profile (landed as `context/mission.md`), conventions, members + style, KB seed, neighbouring
teams, extras.

## Notes

- `context/do-not-propose.md` declined — the repo's boundaries are enforced in `SKILL.md`.
- The anchor has no `context/tooling/knowledge-sources.md`; routing falls back to the copy shipped
  with the awow plugin. Add one to the anchor only to diverge from that contract.
