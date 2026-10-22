"""Curate a reproducible, entirely synthetic Chelsea 2-3 Man City demo.

Run AFTER generate_events and BEFORE match_stats. Real names are used as
fictional actors; no real-world match events or outcomes are asserted.
"""
import json
from pathlib import Path
from src.processing.match_stats import calculate_stats
from src.processing.validate_events import validate_events

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'synthetic'
EVENTS_PATH = DATA / 'match_001.json'
METADATA_PATH = DATA / 'match_001_metadata.json'
STATS_PATH = DATA / 'match_001_stats.json'

# A fixed demo cast, not a claim about current registered squads.
PLAYERS = {
    'HOME': [
        ('Robert Sanchez', 'GK'), ('Reece James', 'DF'), ('Wesley Fofana', 'DF'),
        ('Levi Colwill', 'DF'), ('Marc Cucurella', 'DF'), ('Moises Caicedo', 'MF'),
        ('Enzo Fernandez', 'MF'), ('Cole Palmer', 'FW'), ('Pedro Neto', 'FW'),
        ('Nicolas Jackson', 'FW'), ('Noni Madueke', 'FW'),
    ],
    'AWAY': [
        ('Ederson', 'GK'), ('Kyle Walker', 'DF'), ('Ruben Dias', 'DF'),
        ('Josko Gvardiol', 'DF'), ('John Stones', 'DF'), ('Rodri', 'MF'),
        ('Bernardo Silva', 'MF'), ('Phil Foden', 'FW'), ('Erling Haaland', 'FW'),
        ('Jeremy Doku', 'FW'), ('Kevin De Bruyne', 'MF'),
    ],
}

# This is a fixed historical-style demo cast. Verify squad eligibility separately
# if representing a specific real season. All gameplay remains simulated.
GOALS = [
    (18, 'HOME', 'Cole Palmer'),
    (36, 'AWAY', 'Erling Haaland'),
    (57, 'AWAY', 'Phil Foden'),
    (72, 'HOME', 'Cole Palmer'),
    (86, 'AWAY', 'Erling Haaland'),
]


def main():
    events = json.loads(EVENTS_PATH.read_text(encoding='utf-8'))
    metadata = json.loads(METADATA_PATH.read_text(encoding='utf-8'))
    metadata.setdefault('teams', {})
    names = {'HOME': 'Chelsea', 'AWAY': 'Manchester City'}
    roster = {}
    for team, club in names.items():
        metadata['teams'].setdefault(team, {})['name'] = club
        metadata['teams'][team]['players'] = [
            {'player_id': f'{team}_{i:02d}', 'name': name, 'position': position}
            for i, (name, position) in enumerate(PLAYERS[team], 1)
        ]
        for i, (name, position) in enumerate(PLAYERS[team], 1):
            roster[f'{team}_{i:02d}'] = (name, position)
    metadata['simulation'] = True
    metadata['disclaimer'] = 'Fictional match using real player names; not a real result.'

    # Reset previous goals; preserve the original total number of shots.
    for event in events:
        if event['event_type'] == 'shot' and event['outcome'] == 'goal':
            event['outcome'] = 'saved'

    # Select five distinct existing shots. Move only those events into a
    # deliberate comeback timeline, preserving all other event counts.
    selected_ids = set()
    for minute, team, scorer in GOALS:
        candidates = [e for e in events if e['team_id'] == team
                      and e['event_type'] == 'shot'
                      and e['event_id'] not in selected_ids]
        if not candidates:
            raise ValueError(f'Not enough {team} shots to curate the demo')
        # Prefer originally nearby events to minimise timeline disruption.
        chosen = min(candidates, key=lambda e: (
            abs(e['minute'] - minute), -(e.get('xg') or 0)))
        selected_ids.add(chosen['event_id'])
        chosen['minute'] = minute
        chosen['second'] = 30
        chosen['timestamp_seconds'] = (minute - 1) * 60 + 30
        chosen['outcome'] = 'goal'
        chosen['player_id'] = next(pid for pid, (name, _) in roster.items()
                                   if pid.startswith(team + '_') and name == scorer)
        chosen['possession_team'] = team

    # Give all non-goal events a position-appropriate player. The random event
    # generator's original player IDs are not guaranteed to fit event roles.
    # This changes actor IDs, not event types or outcomes.
    import random
    rng = random.Random(2026)
    for event in events:
        if event['event_id'] not in selected_ids:
            team = event['team_id']
            kind = event['event_type']
            allowed = {
                'shot': {'FW', 'MF'}, 'pass': {'DF', 'MF', 'FW'},
                'corner': {'MF', 'FW'}, 'tackle': {'DF', 'MF'},
                'interception': {'DF', 'MF'}, 'foul': {'DF', 'MF', 'FW'},
            }.get(kind, {'DF', 'MF', 'FW'})
            ids = [pid for pid, (_, pos) in roster.items()
                   if pid.startswith(team + '_') and pos in allowed]
            event['player_id'] = rng.choice(ids)
        event['player_name'] = roster[event['player_id']][0]

    # Chronological order is required by validation and possession calculations.
    events.sort(key=lambda e: (e['timestamp_seconds'], e['event_id']))
    # Possession IDs must be non-decreasing; recompute from the event timeline.
    possession_id, previous = 0, None
    for event in events:
        if event['possession_team'] != previous:
            possession_id += 1
        event['possession_id'] = possession_id
        previous = event['possession_team']

    errors = validate_events(events)
    if errors:
        raise ValueError(f'Validation failed: {errors[:10]}')
    stats = calculate_stats(events)
    assert (stats['HOME']['goals'], stats['AWAY']['goals']) == (2, 3)

    # Write only after all checks pass.
    EVENTS_PATH.write_text(json.dumps(
        events, indent=2) + '\n', encoding='utf-8')
    METADATA_PATH.write_text(json.dumps(
        metadata, indent=2) + '\n', encoding='utf-8')
    STATS_PATH.write_text(json.dumps(stats, indent=2) + '\n', encoding='utf-8')
    print('Chelsea 2-3 Manchester City (SIMULATED)')
    for event in events:
        if event['event_type'] == 'shot' and event['outcome'] == 'goal':
            print(
                f"{event['minute']}' {event['player_name']} — {names[event['team_id']]}")
    print(
        f'Validated {len(events)} synthetic events; saved match, metadata and stats.')


if __name__ == '__main__':
    main()
