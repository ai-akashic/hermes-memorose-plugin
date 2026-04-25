# Hermes Memorose Plugin

Memorose long-term memory provider for Hermes Agent.

This repository is a standalone Hermes memory plugin. Users install it as a plugin repo, provide `MEMOROSE_API_KEY` and `base_url` during Hermes setup, and then select `memorose` as the active memory provider.

## What It Provides

- strict Hermes runtime `user_id` requirement
- direct `session_id -> stream_id` mapping
- Python `memorose` SDK integration
- agent-callable tools for search, store, delete, status, and tasks (invoked by the LLM during a Hermes session, not from the shell)

## Install

Install from a Git repository:

```bash
hermes plugins install ai-akashic/hermes-memorose-plugin
```

Or install from a full Git URL:

```bash
hermes plugins install https://github.com/ai-akashic/hermes-memorose-plugin.git
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

The setup flow will ask for:

```bash
MEMOROSE_API_KEY=your-key
```

It will also ask for the Memorose server `base_url`. If you accept the default, Hermes uses:

```text
http://127.0.0.1:3000
```

Hermes saves the non-secret provider config in `$HERMES_HOME/memorose.json`:

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

### API key handling

`MEMOROSE_API_KEY` is loaded **only from the process environment** (`config.py` reads `os.environ["MEMOROSE_API_KEY"]`). It is intentionally **not** read from `memorose.json` — that file is for non-secret config. Even if you add an `api_key` field to the JSON it will be ignored, and the plugin will still raise `MEMOROSE_API_KEY is required` at load time.

Persist the key the way you would any other secret:

```bash
# user shell
echo 'export MEMOROSE_API_KEY=your-key' >> ~/.bashrc

# or systemd unit
Environment=MEMOROSE_API_KEY=your-key
```

## Runtime Rules

- `user_id` must be supplied by Hermes runtime
- missing `user_id` is a hard error
- Hermes `session_id` becomes Memorose `stream_id`
- non-UUID runtime ids are converted to deterministic UUID5 values before SDK calls
- this plugin does not support alternate stream routing strategies

### UUID normalization

Memorose expects `user_id` and `stream_id` in UUID form. Hermes runtime ids from platforms such as WeChat may be arbitrary strings like `o9cq...@im.wechat`, so the plugin normalizes ids at the service boundary before calling the SDK:

- valid UUID inputs pass through unchanged
- non-UUID inputs are mapped with deterministic `uuid.uuid5(...)`
- `user_id` and `stream_id` use different namespaces (`memorose://user/...` and `memorose://stream/...`) so the same raw string cannot collide across roles

This keeps Hermes-visible runtime ids intact for status/debug output while ensuring Memorose receives stable UUIDs.

## Agent Tools

These are the tools the Hermes LLM can call during an agent session — they are **not** shell commands. They are registered through `provider.py` and dispatched at runtime when the model decides to use them.

- `memorose_search`
- `memorose_store`
- `memorose_delete`
- `memorose_status`
- `memorose_tasks`

## CLI

The plugin exposes a single CLI subcommand, `status`, intended as a health/config self-check:

```bash
hermes memorose status \
  --hermes-home "$HERMES_HOME" \
  --user-id "<user_id>" \
  --session-id "<session_id>"
```

A successful run prints JSON, e.g.:

```json
{
  "pending": 0,
  "ready": true
}
```

There are no `store` / `search` / `delete` CLI subcommands — those operations are only available as agent tools (see above).

## Troubleshooting

**`MemoroseConfigError: MEMOROSE_API_KEY is required`**

The variable is missing from the Python process that runs Hermes. Things to check, in order:

1. `env | grep MEMOROSE_API_KEY` in the same shell you launch `hermes` from.
2. If Hermes is launched via a wrapper (sudo, systemd, supervisor, Docker, etc.), confirm the wrapper passes the variable through. `sudo` strips environment by default — use `sudo -E`, `Defaults env_keep += "MEMOROSE_API_KEY"` in `sudoers`, or pass it explicitly: `sudo MEMOROSE_API_KEY=… /path/to/hermes …`.
3. Inline the value to rule out shell-export issues: `MEMOROSE_API_KEY=… hermes memorose status …`.

The error never indicates a problem with `memorose.json`; the JSON is read independently and the key is not stored there (see *API key handling* above).

## Development

```bash
python -m pytest tests -v
```

## Repository Layout

This repository root is the plugin root expected by Hermes:

```text
hermes-memorose-plugin/
├── plugin.yaml          # manifest: name, version, requires_env, pip_dependencies
├── __init__.py
├── cli.py               # re-exports register_cli / memorose_command
├── memorose_cli.py      # `hermes memorose status` implementation
├── config.py            # loads memorose.json + MEMOROSE_API_KEY env var
├── provider.py          # registers agent tools with the Hermes runtime
├── service.py           # MemoroseService — wraps the memorose Python SDK
├── formatters.py        # tool-result formatting helpers
├── after-install.md     # post-install instructions surfaced by Hermes
├── requirements.txt
├── docs/
├── tests/
├── LICENSE
└── README.md
```
