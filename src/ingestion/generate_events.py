
import json
import random
from pathlib import Path

random.seed(42)

MATCH_ID = "match_001"
HOME_TEAM = "HOME"
AWAY_TEAM = "AWAY"

EVENT_TYPES = [
    "pass",
    "shot",
    "foul",
    "tackle",
    "interception",
    "corner",
]

EVENT_WEIGHTS = [55, 10, 10, 12, 8, 5]


def generate_event(event_id, minute):
    team = random.choice([HOME_TEAM, AWAY_TEAM])
    player_number = random.randint(1, 11)

    event_type = random.choices(
        EVENT_TYPES,
        weights=EVENT_WEIGHTS,
        k=1
    )[0]

    event = {
        "event_id": f"evt_{event_id:04d}",
        "match_id": MATCH_ID,
        "minute": minute,
        "second": random.randint(0, 59),
        "team_id": team,
        "player_id": f"{team}_{player_number:02d}",
        "event_type": event_type,
        "x": round(random.uniform(0, 100), 2),
        "y": round(random.uniform(0, 100), 2),
        "outcome": "successful",
        "xg": None,
    }

    if event_type == "shot":
        event["xg"] = round(random.uniform(0.02, 0.6), 3)
        event["outcome"] = random.choices(
            ["goal", "saved", "off_target"],
            weights=[10, 40, 50],
            k=1
        )[0]

    return event


def generate_match():
    events = []
    event_id = 1

    for minute in range(1, 91):
        num_events = random.randint(2, 5)

        for _ in range(num_events):
            events.append(generate_event(event_id, minute))
            event_id += 1

    events.sort(
        key=lambda event: (
            event["minute"],
            event["second"],
            event["event_id"]
        )
    )

    return events


if __name__ == "__main__":
    events = generate_match()

    output_path = Path("data/synthetic/match_001.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(events, file, indent=2)

    print(f"Generated {len(events)} events")
    print(f"Saved to {output_path}")
