# Hermes Memorose Plugin Design

## Goal

Build a standalone Hermes memory provider plugin named `memorose` that connects Hermes Agent to an already running Memorose server using `base_url` and `api_key`.

The plugin should be installable as a normal Hermes memory provider and should reuse the existing Python Memorose SDK instead of reimplementing the HTTP client.

## Scope

### In scope

- A standalone Python project named `hermes-memorose-plugin`
- Hermes memory provider implementation using the `MemoryProvider` ABC
- Runtime integration with `memorose-sdk/python`
- Prompt-time recall via Memorose retrieve
- Turn sync from Hermes into Memorose ingest
- Explicit memory tools for search, store, delete, status, and tasks
- Hermes setup integration through `get_config_schema()` and `save_config()`
- Optional provider CLI commands through `cli.py`

### Out of scope

- Starting, embedding, or managing the Memorose server process
- Reimplementing the Memorose HTTP client
- Supporting multiple stream strategies in the first version
- OpenClaw compatibility
- Local persistent retry queues or advanced offline buffering

## Product Constraints

### Memorose server boundary

The plugin connects to an already running Memorose server. It does not bootstrap Docker, start binaries, or provision infrastructure.

### User identity

`user_id` must come from Hermes runtime initialization kwargs.

Rules:

- `user_id` is required
- missing `user_id` is a hard runtime error
- no fallback to profile name, session id, static defaults, or generated ids

This intentionally limits the first version to Hermes gateway-style contexts where Hermes provides a stable external user identity.

### Stream identity

The first version supports exactly one stream mapping:

- `stream_id = session_id`

Rules:

- Hermes `session_id` maps directly to Memorose `stream_id`
- there is no `stream_strategy` setting in v1
- there is no fallback or alternate mapping mode

This keeps the first version deterministic and avoids ambiguous per-platform thread identity logic.

## Expected Memory Behavior

Using `session_id` as `stream_id` means each Hermes session writes to its own Memorose stream.

This does **not** mean higher-order memory is fully isolated per session.

Memorose retrieval is user-centered in practice:

- raw ingest is written against a user and a stream
- retrieval calls include a stream id in the route
- current server-side search behavior is fundamentally keyed by `user_id`
- tasks and higher-order graph/community memory are largely user-scoped

Operationally, this means:

- L0/raw event flow is session-shaped
- consolidated memory can still be recalled across sessions for the same user
- task and graph views remain meaningfully shared at the user level

This is acceptable for the first version because it provides clean session ingestion while preserving user-level long-term memory emergence.

## Architecture

The project uses a Provider + Service split.

### `__init__.py`

Responsibilities:

- implement the Hermes `MemoryProvider`
- translate Hermes lifecycle hooks into service calls
- expose tool schemas
- dispatch tool calls
- register the provider through `register(ctx)`

### `service.py`

Responsibilities:

- wrap `memorose-sdk/python`
- provide typed high-level operations for the provider
- centralize SDK error handling and response normalization
- build Memorose ingest/retrieve/task/delete requests

### `config.py`

Responsibilities:

- load `$HERMES_HOME/memorose.json`
- validate non-secret config values
- resolve secrets from environment
- expose a resolved runtime config object

### `formatters.py`

Responsibilities:

- format prefetch context injected into Hermes prompts
- format tool output payloads
- keep prompt text small and deterministic

### `cli.py`

Responsibilities:

- optional provider-specific CLI subtree
- expose status/debug helpers such as `hermes memorose status`

## Project Layout

```text
hermes-memorose-plugin/
├── README.md
├── requirements.txt
├── plugin.yaml
├── __init__.py
├── service.py
├── config.py
├── formatters.py
├── cli.py
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-22-hermes-memorose-plugin-design.md
```

## Dependencies

Primary runtime dependency:

- `memorose-sdk/python`

Secondary runtime dependencies:

- minimal helper libraries only if necessary
- avoid introducing heavy frameworks

The plugin should prefer the SDK as the source of truth for request and response models.

## Configuration Model

### Secret config

Written to Hermes `.env`:

- `MEMOROSE_API_KEY`

### Non-secret config

Written to `$HERMES_HOME/memorose.json`:

- `base_url`
- `org_id` (optional)
- `retrieve.limit`
- `retrieve.min_score`
- `retrieve.graph_depth`
- `sync.mode`

Recommended v1 defaults:

- `base_url = http://127.0.0.1:3000`
- `retrieve.limit = 8`
- `retrieve.min_score = 0.0`
- `retrieve.graph_depth = 1`
- `sync.mode = user_only`

### `sync.mode`

Supported values:

- `user_only`
- `user_and_assistant`

Default:

- `user_only`

Rationale:

- avoids assistant self-poisoning
- keeps first-version ingest behavior conservative

## Hermes Hook Mapping

### `initialize(session_id, **kwargs)`

Responsibilities:

- require `user_id`
- load resolved config
- create the Memorose service
- bind Hermes `session_id` as the active Memorose `stream_id`

Failure cases:

- missing `user_id`
- missing API key
- invalid base URL
- SDK import failure

### `system_prompt_block()`

Return lightweight provider instructions only, for example:

- what the provider does
- when the model should use explicit memorose tools

This block must remain static and small.

### `prefetch(query, session_id="")`

Responsibilities:

- call Memorose retrieve for the current `user_id` and `stream_id`
- format prompt-safe recall text
- return empty string if no useful results exist

The plugin should keep this conservative and avoid dumping raw payloads into the prompt.

### `sync_turn(user_content, assistant_content, session_id="")`

Responsibilities:

- ingest the user message always
- ingest assistant content only when `sync.mode = user_and_assistant`
- use the runtime `user_id`
- use Hermes `session_id` as Memorose `stream_id`

This should be non-blocking from Hermes' point of view. If a background thread is needed, keep it simple and in-process.

### `on_session_end(messages)`

Initial version behavior:

- no special summarization pass
- optional best-effort final flush if a background write is outstanding

Do not introduce extra LLM extraction logic here; Memorose already owns its own memory pipeline.

### `on_memory_write(action, target, content)`

Optional in v1.

If implemented, mirror explicit Hermes built-in memory writes into Memorose as normal ingest events tagged as user-authored memory actions.

This is a useful integration seam, but it is not required for the first minimal release.

## Tool Surface

The first version should expose the following provider tools:

- `memorose_search`
- `memorose_store`
- `memorose_delete`
- `memorose_status`
- `memorose_tasks`

### `memorose_search`

Purpose:

- explicit semantic lookup

Implementation:

- call Memorose retrieve
- return normalized JSON with top hits, ids, scores, and compact snippets

### `memorose_store`

Purpose:

- explicit memory write initiated by the model

Implementation:

- ingest supplied content into the current user/session stream

### `memorose_delete`

Purpose:

- delete a memory by id

Implementation:

- call SDK delete endpoint for the current `user_id`

### `memorose_status`

Purpose:

- verify connectivity and show active routing context

Implementation:

- report base URL
- report current `user_id`
- report current `stream_id`
- report pending status via Memorose status endpoint

### `memorose_tasks`

Purpose:

- inspect user-level task state

Implementation:

- call user-level task tree and ready task endpoints

## SDK Adapter Design

`service.py` should hide SDK specifics from the provider.

Suggested interface:

- `search_memories(query: str) -> list[...]`
- `store_text(content: str) -> dict`
- `delete_memory(memory_id: str) -> dict`
- `get_status() -> dict`
- `get_tasks() -> dict`

The provider should not construct raw SDK payloads inline.

## Error Handling

Principles:

- configuration errors should fail early and clearly
- missing `user_id` should be explicit and non-recoverable
- SDK/network errors should be surfaced as tool errors or logged warnings
- recall failure should not crash the whole agent turn if it can be degraded safely

Recommended behavior:

- `initialize()` raises on missing `user_id` or unusable config
- `prefetch()` returns empty string on transient retrieve failure, with logging
- explicit tools return structured error JSON on SDK failure

## Testing Strategy

### Unit tests

- config loading and validation
- `user_id` hard-fail behavior
- `session_id -> stream_id` mapping
- formatter output size and structure
- tool dispatch behavior

### Integration tests

Using a mocked `MemoroseClient`:

- provider initialize
- prefetch retrieve flow
- sync turn ingest flow
- delete/status/tasks flow

### Live tests

Optional but recommended:

- run against a locally running Memorose server
- use the existing smoke setup patterns already validated in sibling repos

## Rollout Plan

### Phase 1

- standalone plugin skeleton
- config and SDK wiring
- prefetch + sync_turn
- search/store/status tools

### Phase 2

- delete and tasks tools
- provider CLI commands
- tighter tests

### Phase 3

- mirror Hermes built-in memory writes
- optional richer task/graph surfacing

## Risks

### Missing gateway `user_id`

This is the biggest intentional limitation in v1. CLI sessions without a runtime `user_id` will fail.

This is acceptable because the design explicitly chooses correctness over silent fallback.

### SDK coupling

Using `memorose-sdk/python` means plugin behavior tracks SDK changes.

This is mitigated by the service layer, which keeps the provider surface stable.

### Prompt bloat

Raw retrieve results can get verbose.

This is mitigated by keeping formatter logic compact and limiting the number of injected hits.

## Decisions Finalized

- Plugin language: Python
- Integration style: Hermes memory provider plugin
- Client layer: reuse `memorose-sdk/python`
- Architecture: Provider + Service split
- `user_id`: required from Hermes runtime, no fallback
- `stream_id`: exactly `session_id`
- No stream strategy selection in v1
- Default sync mode: `user_only`
