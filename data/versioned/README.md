# Versioned match statistics

This directory contains Git-friendly snapshots generated from the local SQLite
database. Snapshots contain only aggregated champion and same-role matchup
counts. Riot IDs, PUUIDs, match IDs, API keys, and exact timestamps are never
exported.

Refresh snapshots after collecting matches:

```bash
python3 scripts/export_match_stats.py
git add data/versioned
```

Each JSON file is scoped to one patch and queue. `games` and `wins` are stored
instead of a rounded win rate so consumers can apply their own sample-size
smoothing.
