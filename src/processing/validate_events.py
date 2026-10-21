
import json
from pathlib import Path

REQUIRED_FIELDS = [
    "event_id", "match_id", "minute", "second",
    "team_id", "player_id", "event_type",
    "x", "y", "outcome", "xg"
]

VALID_TYPES = {
    "pass", "shot", "foul",
    "tackle", "interception", "corner"
}


def validate_events(events):
    errors = []
    seen_ids = set()

    for index, event in enumerate(events):
        missing = [f for f in REQUIRED_FIELDS if f not in event]

        if missing:
            errors.append(f"Event {index}: missing {missing}")
            continue

        event_id = event["event_id"]

        if event_id in seen_ids:
            errors.append(f"Duplicate event ID: {event_id}")
        seen_ids.add(event_id)

        if event["event_type"] not in VALID_TYPES:
            errors.append(f"{event_id}: invalid event type")

        if not isinstance(event["minute"], int) or not 1 <= event["minute"] <= 90:
            errors.append(f"{event_id}: invalid minute")

        if not isinstance(event["second"], int) or not 0 <= event["second"] <= 59:
            errors.append(f"{event_id}: invalid second")

        for coordinate in ("x", "y"):
            value = event[coordinate]
            if not isinstance(value, (int, float)) or not 0 <= value <= 100:
                errors.append(f"{event_id}: invalid {coordinate}")

        if event["team_id"] not in {"HOME", "AWAY"}:
            errors.append(f"{event_id}: invalid team")

        if event["event_type"] == "shot":
            xg = event["xg"]
            if not isinstance(xg, (int, float)) or not 0 <= xg <= 1:
                errors.append(f"{event_id}: invalid shot xG")
        elif event["xg"] is not None:
            errors.append(f"{event_id}: unexpected xG")

    return errors


if __name__ == "__main__":
    path = Path("data/synthetic/match_001.json")

    with path.open(encoding="utf-8") as file:
        events = json.load(file)

    errors = validate_events(events)

    if errors:
        print(f"Validation failed: {len(errors)} errors")
        for error in errors[:20]:
            print(error)
        raise SystemExit(1)

    print(f"Validation passed: {len(events)} events")
