# Install DUCAT for a team

A committed setting registers the marketplace and pre-enables the plugin for everyone who opens this
repository. It does not install it for them: Claude Code never installs a plugin from an external
source on a teammate's behalf. Each person runs one command.

## What is committed

`.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "ducat": {
      "source": {
        "source": "git",
        "url": "https://github.com/CauchyIO/ducat.git",
        "ref": "plugin"
      }
    }
  },
  "enabledPlugins": { "ducat@ducat": true }
}
```

`extraKnownMarketplaces` registers the catalog. The `ref` pins it to the `plugin` branch, which is
where the manifest lives — the default branch does not carry one. `enabledPlugins` turns the plugin
on the moment it is installed, so nobody has to enable it by hand.

## What a teammate does

Open the repository in Claude Code, accept the trust prompt, then:

```
/plugin install ducat@ducat
```

`/plugin` shows whether it is installed and enabled; `/mcp` shows whether `databricks-sql` is
connected.

## What the trust prompt asks

Claude Code does not read a repository's settings until someone confirms the folder is trusted,
because those settings can register a marketplace and enable plugins — and a plugin runs code on the
machine with that person's own privileges. Trusting this folder accepts that DUCAT's marketplace is
registered from `CauchyIO/ducat` and that the plugin is enabled once installed.

It grants no access to any Databricks workspace. That needs the credentials below.

## The two variables the connection needs

The plugin's `.mcp.json` reads both from the shell Claude Code starts in.

| Variable | Carries |
|---|---|
| `DATABRICKS_MCP_URL` | `https://<workspace-hostname>/api/2.0/mcp/sql` |
| `DATABRICKS_SP_TOKEN` | The read-only service principal's token |

Neither is committed, and neither belongs on disk in cleartext.
[`connect-mcp-server.md`](connect-mcp-server.md) sets both without a secret touching a file. Without
them the plugin loads and every query fails.
