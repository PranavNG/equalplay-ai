"""Aggregate synthetic event-level match statistics."""
import json
from pathlib import Path
from src.processing.validate_events import validate_events

INPUT = Path("data/synthetic/match_001.json")
METADATA = Path("data/synthetic/match_001_metadata.json")
OUTPUT = Path("data/synthetic/match_001_stats.json")


def calculate_stats(events):
    stats = {
        team: {
            "goals": 0, "shots": 0, "shots_on_target": 0, "xg": 0.0,
            "passes": 0, "completed_passes": 0, "pass_accuracy": 0.0,
            "possession": None, "corners": 0, "fouls": 0,
            "yellow_cards": 0, "red_cards": 0, "tackles": 0,
            "interceptions": 0, "events": 0, "event_share": 0.0,
        }
        for team in ("HOME", "AWAY")
    }
    for event in events:
        s = stats[event["team_id"]]
        kind, outcome = event["event_type"], event["outcome"]
        s["events"] += 1
        if kind == "shot":
            s["shots"] += 1
            s["xg"] += event["xg"]
            s["shots_on_target"] += outcome in ("goal", "saved")
            s["goals"] += outcome == "goal"
        elif kind == "pass":
            s["passes"] += 1
            s["completed_passes"] += outcome == "successful"
        elif kind == "corner":
            s["corners"] += 1
        elif kind == "foul":
            s["fouls"] += 1
            if event["card"] == "yellow":
                s["yellow_cards"] += 1
            elif event["card"] == "red":
                s["red_cards"] += 1
        elif kind == "tackle":
            s["tackles"] += outcome == "successful"
        elif kind == "interception":
            s["interceptions"] += outcome == "successful"

    for s in stats.values():
        s["xg"] = round(s["xg"], 2)
        s["pass_accuracy"] = round(
            100 * s["completed_passes"] / s["passes"], 1) if s["passes"] else 0.0
        s["event_share"] = round(
            100 * s["events"] / len(events), 1) if events else 0.0

    # Approximate simulated possession from the time between consecutive events.
    # The last event's interval is counted up to the end of regulation (90:00).
    if events:
        durations = {"HOME": 0, "AWAY": 0}
        for i, event in enumerate(events):
            start = event["timestamp_seconds"]
            end = events[i + 1]["timestamp_seconds"] if i + \
                1 < len(events) else 5400
            durations[event["possession_team"]] += max(0, end - start)
        total = sum(durations.values())
        if total:
            home_pct = round(100 * durations["HOME"] / total, 1)
            stats["HOME"]["possession"] = home_pct
            stats["AWAY"]["possession"] = round(100 - home_pct, 1)
    return stats


if __name__ == "__main__":
    with INPUT.open(encoding="utf-8") as file:
        events = json.load(file)
    errors = validate_events(events)
    if errors:
        raise ValueError(f"Invalid events: {errors[:10]}")
    stats = calculate_stats(events)
    with METADATA.open(encoding="utf-8") as file:
        metadata = json.load(file)
    for team_id, s in stats.items():
        print(f"\n{metadata['teams'][team_id]['name']}")
        for key, value in s.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as file:
        json.dump(stats, file, indent=2)
    print(f"\nSaved statistics to {OUTPUT}")
