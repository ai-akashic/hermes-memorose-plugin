# Hermes Memorose Plugin

Memorose long-term memory provider for Hermes Agent.

This repository is a standalone Hermes memory plugin. Users install it as a plugin repo, point it at a Memorose server with `MEMOROSE_API_KEY` and `base_url`, and then select `memorose` as the active memory provider.

## What It Provides

- strict Hermes runtime `user_id` requirement
- direct `session_id -> stream_id` mapping
- Python `memorose` SDK integration
- explicit tools for search, store, delete, status, and tasks

## Install

Install from a Git repository:

```bash
hermes plugins install <owner>/hermes-memorose-plugin
```

Or install from a full Git URL:

```bash
hermes plugins install https://github.com/<owner>/hermes-memorose-plugin.git
```

The installer uses `plugin.yaml` and installs the plugin as `memorose`.

## Configure

Run the Hermes memory provider setup flow:

```bash
hermes memory setup
```

Then select `memorose`.

You can also activate it manually:

```bash
hermes config set memory.provider memorose
```

The installer or setup flow will ask for:

```bash
MEMOROSE_API_KEY=your-key
```

Optional provider config lives in `$HERMES_HOME/memorose.json`:

```json
{
  "base_url": "http://127.0.0.1:3000",
  "retrieve": {
    "limit": 8,
    "min_score": 0.0,
    "graph_depth": 1
  },
  "sync": {
    "mode": "user_only"
  }
}
```

## Runtime Rules

- `user_id` must be supplied by Hermes runtime
- missing `user_id` is a hard error
- Hermes `session_id` becomes Memorose `stream_id`
- this plugin does not support alternate stream routing strategies

## Tools

- `memorose_search`
- `memorose_store`
- `memorose_delete`
- `memorose_status`
- `memorose_tasks`

## CLI

When `memorose` is the active memory provider, Hermes exposes:

```bash
hermes memorose status --hermes-home "$HERMES_HOME" --user-id "<user_id>" --session-id "<session_id>"
```

## Development

```bash
/Users/dylan/.pyenv/versions/3.12.10/bin/pytest tests -v
```

## Repository Layout

This repository root is the plugin root expected by Hermes:

```text
hermes-memorose-plugin/
├── plugin.yaml
├── __init__.py
├── cli.py
├── provider.py
├── service.py
└── README.md
```
