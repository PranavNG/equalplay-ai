
import json
from pathlib import Path

from src.processing.validate_events import validate_events


def calculate_stats(events):
    stats = {
        team: {
            "goals": 0,
            "shots": 0,
            "shots_on_target": 0,
            "xg": 0.0,
            "passes": 0,
            "completed_passes": 0,
            "events": 0,
        }
        for team in ("HOME", "AWAY")
    }

    for event in events:
        team_stats = stats[event["team_id"]]
        event_type = event["event_type"]
        outcome = event["outcome"]

        team_stats["events"] += 1

        if event_type == "shot":
            team_stats["shots"] += 1
            team_stats["xg"] += event["xg"]

            if outcome in ("goal", "saved"):
                team_stats["shots_on_target"] += 1

            if outcome == "goal":
                team_stats["goals"] += 1

        elif event_type == "pass":
            team_stats["passes"] += 1
            if outcome == "successful":
                team_stats["completed_passes"] += 1

    total_events = len(events)

    for team_stats in stats.values():
        passes = team_stats["passes"]

        team_stats["xg"] = round(team_stats["xg"], 2)
        team_stats["pass_accuracy"] = round(
            100 * team_stats["completed_passes"] / passes, 1
        ) if passes else 0.0

        team_stats["event_share"] = round(
            100 * team_stats["events"] / total_events, 1
        ) if total_events else 0.0

    return stats


if __name__ == "__main__":
    input_path = Path("data/synthetic/match_001.json")

    with input_path.open(encoding="utf-8") as file:
        events = json.load(file)

    errors = validate_events(events)
    if errors:
        raise ValueError(f"Invalid match data: {errors[:5]}")

    stats = calculate_stats(events)

    output_path = Path("data/synthetic/match_001_stats.json")

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(stats, file, indent=2)

    metadata_path = Path("data/synthetic/match_001_metadata.json")

    with metadata_path.open(encoding="utf-8") as file:
        metadata = json.load(file)

    for team_id, team_stats in stats.items():
        team_name = metadata["teams"][team_id]["name"]

        print(f"\n{team_name}")
        print(f"Goals: {team_stats['goals']}")
        print(f"Shots: {team_stats['shots']}")
        print(f"Shots on target: {team_stats['shots_on_target']}")
        print(f"xG: {team_stats['xg']}")
        print(f"Pass accuracy: {team_stats['pass_accuracy']}%")
        print(f"\nSaved statistics to {output_path}")
