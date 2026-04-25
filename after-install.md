# Memorose Plugin Installed

## Next steps

1. Run `hermes memory setup`
2. Select `memorose`
3. Export `MEMOROSE_API_KEY` in your shell (see *API key* below)
4. Provide the Memorose `base_url` during setup, or accept the default `http://127.0.0.1:3000`

Manual activation (skips the wizard):

```bash
hermes config set memory.provider memorose
```

## Config file

Non-secret config is saved to `$HERMES_HOME/memorose.json`:

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

## API key

`MEMOROSE_API_KEY` is read **only from the process environment**, never from `memorose.json`. Persist it the way you would any other secret:

```bash
echo 'export MEMOROSE_API_KEY=your-key' >> ~/.bashrc
```

If Hermes runs under `sudo` / systemd / Docker, make sure the wrapper passes the variable through — `sudo` strips it by default.

## Verify

```bash
hermes memorose status \
  --hermes-home "$HERMES_HOME" \
  --user-id "<user_id>" \
  --session-id "<session_id>"
```

Expected output:

```json
{
  "pending": 0,
  "ready": true
}
```
