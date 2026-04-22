# Memorose Plugin Installed

Next steps:

1. Run `hermes memory setup`
2. Select `memorose`
3. Provide `MEMOROSE_API_KEY`
4. Set `base_url` in `$HERMES_HOME/memorose.json` if your Memorose server is not `http://127.0.0.1:3000`

Manual activation:

```bash
hermes config set memory.provider memorose
```

Optional config file:

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
