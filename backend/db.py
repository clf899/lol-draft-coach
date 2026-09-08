import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from .catalog import ROOT

@contextmanager
def connect():
    path = Path(os.environ.get('DRAFT_DB', str(ROOT/'data/runtime/draft.db')))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA journal_mode=WAL')
    connection.executescript('''
      CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS pool (champion_id TEXT NOT NULL, role TEXT NOT NULL, comfort INTEGER NOT NULL CHECK(comfort BETWEEN 1 AND 5), PRIMARY KEY(champion_id,role));
      CREATE TABLE IF NOT EXISTS matches (match_id TEXT NOT NULL, puuid TEXT NOT NULL, champion_id TEXT NOT NULL, role TEXT NOT NULL, queue INTEGER NOT NULL, win INTEGER NOT NULL CHECK(win IN (0,1)), played_at REAL NOT NULL, PRIMARY KEY(match_id,puuid));
      CREATE INDEX IF NOT EXISTS idx_match_player_queue_time ON matches(puuid,queue,played_at);
    ''')
    try:
        with connection:
            yield connection
    finally:
        connection.close()

def preference(key, default=None):
    with connect() as db:
        row = db.execute('SELECT value FROM preferences WHERE key=?', (key,)).fetchone()
    return json.loads(row['value']) if row else default

def set_preference(key,value):
    with connect() as db:
        db.execute('INSERT INTO preferences(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key,json.dumps(value)))

def pool():
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT * FROM pool ORDER BY role,champion_id')]

def statistics(queue=420, now=None):
    now = now or time.time()
    account = preference('account', {})
    with connect() as db:
        rows = db.execute('SELECT * FROM matches WHERE puuid=? AND queue=? AND played_at>=?', (account.get('puuid',''),queue,now-90*86400)).fetchall()
    stats = {}
    for row in rows:
        key = (row['champion_id'],row['role'])
        s = stats.setdefault(key, {'games':0,'wins':0,'weighted_games':0.,'weighted_wins':0.,'last_played':0})
        weight = 0.5 ** (max(0,now-row['played_at'])/(30*86400))
        s['games'] += 1; s['wins'] += row['win']
        s['weighted_games'] += weight; s['weighted_wins'] += weight*row['win']
        s['last_played'] = max(s['last_played'], row['played_at'])
    return stats
