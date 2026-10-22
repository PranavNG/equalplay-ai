"""Validate the synthetic event schema and event chronology."""
import json
from pathlib import Path

REQUIRED = {
    "event_id", "match_id", "minute", "second", "timestamp_seconds",
    "team_id", "player_id", "event_type", "outcome", "x", "y",
    "xg", "possession_team", "possession_id", "card"
}
TYPES = {"pass", "shot", "tackle", "interception", "foul", "corner"}
TEAMS = {"HOME", "AWAY"}
OUTCOMES = {
    "pass": {"successful", "failed"},
    "shot": {"goal", "saved", "off_target", "blocked"},
    "tackle": {"successful"},
    "interception": {"successful"},
    "foul": {"committed"},
    "corner": {"awarded"},
}


def validate_events(events):
    errors = []
    if not isinstance(events, list):
        return ["Events must be a JSON array"]
    seen = set()
    previous_time = -1
    previous_possession_id = 0
    for i, e in enumerate(events):
        if not isinstance(e, dict):
            errors.append(f"Event {i}: expected object")
            continue
        missing = REQUIRED - e.keys()
        if missing:
            errors.append(f"Event {i}: missing {sorted(missing)}")
            continue
        eid = e["event_id"]
        if not isinstance(eid, str) or not eid:
            errors.append(f"Event {i}: invalid event_id")
        elif eid in seen:
            errors.append(f"Duplicate event ID: {eid}")
        seen.add(eid)
        if not isinstance(e["match_id"], str) or not e["match_id"]:
            errors.append(f"{eid}: invalid match_id")
        minute, second, t = e["minute"], e["second"], e["timestamp_seconds"]
        if type(minute) is not int or not 1 <= minute <= 90:
            errors.append(f"{eid}: invalid minute")
        if type(second) is not int or not 0 <= second <= 59:
            errors.append(f"{eid}: invalid second")
        if type(t) is not int or t < 0 or t >= 5400:
            errors.append(f"{eid}: invalid timestamp_seconds")
        elif type(minute) is int and type(second) is int and t != (minute - 1) * 60 + second:
            errors.append(f"{eid}: timestamp doesn't match minute/second")
        elif t < previous_time:
            errors.append(f"{eid}: events out of chronological order")
        if type(t) is int:
            previous_time = t
        if e["team_id"] not in TEAMS or e["possession_team"] not in TEAMS:
            errors.append(f"{eid}: invalid team")
        if not isinstance(e["player_id"], str) or not e["player_id"]:
            errors.append(f"{eid}: invalid player_id")
        kind = e["event_type"]
        if kind not in TYPES:
            errors.append(f"{eid}: invalid event type")
        elif e["outcome"] not in OUTCOMES[kind]:
            errors.append(f"{eid}: invalid outcome for {kind}")
        for coord in ("x", "y"):
            value = e[coord]
            if type(value) not in (int, float) or not 0 <= value <= 100:
                errors.append(f"{eid}: invalid {coord}")
        if kind == "shot":
            if type(e["xg"]) not in (int, float) or not 0 <= e["xg"] <= 1:
                errors.append(f"{eid}: invalid shot xG")
        elif e["xg"] is not None:
            errors.append(f"{eid}: xG should be null for non-shots")
        if e["card"] not in (None, "yellow", "red") or (e["card"] is not None and kind != "foul"):
            errors.append(f"{eid}: invalid card")
        pid = e["possession_id"]
        if type(pid) is not int or pid < 1 or pid < previous_possession_id:
            errors.append(f"{eid}: invalid possession_id")
        if type(pid) is int:
            previous_possession_id = pid
        if kind in {"tackle", "interception", "foul"} and e["team_id"] == e["possession_team"]:
            errors.append(
                f"{eid}: defensive event attributed to possession team")
        if kind in {"pass", "shot", "corner"} and e["team_id"] != e["possession_team"]:
            errors.append(f"{eid}: attacking event attributed to other team")
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
