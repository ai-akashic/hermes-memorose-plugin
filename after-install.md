# Memorose Plugin Installed

Next steps:

1. Run `hermes memory setup`
2. Select `memorose`
3. Provide `MEMOROSE_API_KEY`
4. Provide the Memorose `base_url` during setup, or accept the default `http://127.0.0.1:3000`

Manual activation:

```bash
hermes config set memory.provider memorose
```

Hermes saves the non-secret provider config in:

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
