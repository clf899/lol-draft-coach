#!/usr/bin/env python3
"""Export reviewable, anonymous match aggregates for Git version control."""
import argparse
import json
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', type=Path, default=Path('data/runtime/draft.db'))
    parser.add_argument('--out', type=Path, default=Path('data/versioned'))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(args.db)
    connection.row_factory = sqlite3.Row
    dimensions = connection.execute('''
      SELECT DISTINCT patch,queue FROM matches
      WHERE patch != '' ORDER BY patch,queue
    ''').fetchall()
    expected = set()
    for dimension in dimensions:
        patch, queue = dimension['patch'], dimension['queue']
        champions = [dict(row) for row in connection.execute('''
          SELECT role,champion_id,COUNT(*) AS games,SUM(win) AS wins
          FROM matches WHERE patch=? AND queue=?
          GROUP BY role,champion_id ORDER BY role,champion_id
        ''',(patch,queue))]
        matchups = [dict(row) for row in connection.execute('''
          SELECT role,champion_id,opponent_champion_id,COUNT(*) AS games,SUM(win) AS wins
          FROM matches
          WHERE patch=? AND queue=? AND opponent_champion_id IS NOT NULL
          GROUP BY role,champion_id,opponent_champion_id
          ORDER BY role,champion_id,opponent_champion_id
        ''',(patch,queue))]
        payload = {
            'format_version': 1,
            'patch': patch,
            'queue': queue,
            'participant_rows': sum(row['games'] for row in champions),
            'champions': champions,
            'matchups': matchups,
        }
        target = args.out/f'match-stats-{patch}-q{queue}.json'
        target.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        expected.add(target.name)
        print(f'wrote {target} ({payload["participant_rows"]} rows)')
    connection.close()

    for old in args.out.glob('match-stats-*-q*.json'):
        if old.name not in expected:
            old.unlink()


if __name__ == '__main__':
    main()
