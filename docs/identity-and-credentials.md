# Identity and credentials

Which identity a command runs as, and how to change it back.

Two identities now exist on this machine. Confusing them produced a false result during CAU-1350,
so this note records how the CLI chooses and how to undo the choice.

## The two identities

| Identity | How it authenticates | What it can do |
|---|---|---|
| Your own login | OAuth U2M, profile in `~/.databrickscfg`, token in the OS keyring | Workspace admin. Reads and **writes**. |
| `sp-databricks-cost-optimizer` | OAuth M2M, client ID and secret | Reads `system` only. No write anywhere. |

Identifiers are in `environment.local.md`, which git ignores.

## How the CLI decides

The CLI resolves credentials in this order, first match winning:

1. Explicit flags on the command.
2. `DATABRICKS_*` environment variables.
3. The profile named by `-p` or `DATABRICKS_CONFIG_PROFILE`.
4. The `DEFAULT` profile.

Environment variables sit **above** the profile. Exporting `DATABRICKS_CLIENT_ID` and
`DATABRICKS_CLIENT_SECRET` from `~/.zshrc` therefore makes every command in every future shell run
as the service principal, including administration you meant to run as yourself. That was the
earlier instruction, and it was the wrong shape.

## What went wrong

The environment variables were never set, so the read and write probes both ran as
your own login. `CREATE TABLE` succeeded, a table was created in `<workspace-catalog>.default`, and the
read-only boundary was never tested.

## Revert

Nothing persistent was changed unless you edited `~/.zshrc`. Check and clear:

```sh
env | grep DATABRICKS          # expect no output
grep DATABRICKS ~/.zshrc       # remove any export lines found
unset DATABRICKS_HOST DATABRICKS_CLIENT_ID DATABRICKS_CLIENT_SECRET
databricks auth describe       # expect your own user, not the principal
```

The keychain entry is inert on its own — it is read only by a command that asks for it.

## The safer pattern

Scope the principal to single commands instead of the whole shell. In `~/.zshrc`:

```sh
dbsp() {
  DATABRICKS_HOST="https://<workspace-hostname>" \
  DATABRICKS_CLIENT_ID="<application-id>" \
  DATABRICKS_CLIENT_SECRET="$(security find-generic-password -a "$USER" -s databricks-cost-optimizer-sp -w)" \
  databricks "$@"
}
```

`databricks ...` stays you. `dbsp ...` is the principal. `dbsp auth describe` should print
`oauth-m2m` and the application ID — if it prints your email, the credential did not load.

## Update 2026-08-24: three identities, not two

A third identity now exists — a personal access token the service principal minted for itself. The
principal has two credentials, used for different things:

| Credential | Used by | Reaches |
|---|---|---|
| OAuth M2M client ID and secret | the `dbsp` shell function | the CLI and the REST APIs |
| Personal access token | Claude Code's MCP client | the managed SQL MCP server |

Both authenticate as the same principal and carry the same read-only grants. Two exist because
Claude Code's MCP client sends a static bearer header, and an M2M access token expires hourly.

Both live in the OS keychain, under `databricks-cost-optimizer-sp` and
`databricks-cost-optimizer-pat`. `DATABRICKS_SP_TOKEN` is deliberately not named
`DATABRICKS_TOKEN` — the latter is read by the CLI's own auth resolution and would make every
`databricks` command run as the principal, which is the trap this log already describes.

Both were pasted into a Claude Code conversation during setup and both should be rotated.

### Two failures worth remembering

**A shell comment reached a keychain prompt.** `security add-generic-password … -w` with a trailing
`# comment` on the pasted line stored `#` as the secret. The symptom was a generic MCP connection
failure. `echo "len=${#VAR}"` diagnoses it in one line.

**Environment variables must exist before Claude Code starts.** It reads them from the launching
process, so a session started before the exports cannot see them, and no amount of approving the
server helps.
