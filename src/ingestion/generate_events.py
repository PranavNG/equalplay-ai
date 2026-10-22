"""Generate reproducible, fictional football events for EqualPlay AI."""
import json
import math
import random
from pathlib import Path

RNG = random.Random(42)
MATCH_ID = "match_001"
TEAMS = ("HOME", "AWAY")
OUTPUT = Path("data/synthetic/match_001.json")


def opponent(team):
    return "AWAY" if team == "HOME" else "HOME"


def calculate_xg(x, y):
    distance = math.hypot(100 - x, 50 - y)
    return round(max(0.01, min(0.75, 0.65 * math.exp(-distance / 18))), 3)


def generate_match():
    events = []
    possession = RNG.choice(TEAMS)
    possession_id = 1
    event_id = 1
    scores = {team: 0 for team in TEAMS}
    cards = {team: {"yellow": 0, "red": 0} for team in TEAMS}

    for minute in range(1, 91):
        count = RNG.randint(3, 6)
        for second in sorted(RNG.sample(range(60), count)):
            before = possession
            kind = RNG.choices(
                ["pass", "shot", "tackle", "interception", "foul", "corner"],
                weights=[68, 7, 9, 7, 6, 3], k=1
            )[0]
            # Tackles, interceptions, and fouls are committed by the defending side.
            actor = opponent(before) if kind in {
                "tackle", "interception", "foul"} else before
            x = round(RNG.uniform(0, 100), 2)
            y = round(RNG.uniform(0, 100), 2)
            outcome = "successful"
            xg = None
            card = None

            if kind == "pass":
                outcome = "successful" if RNG.random() < 0.82 else "failed"
                if outcome == "failed":
                    possession = opponent(before)
            elif kind == "shot":
                x = round(RNG.uniform(70, 98), 2)
                y = round(RNG.uniform(20, 80), 2)
                xg = calculate_xg(x, y)
                if RNG.random() < xg:
                    outcome = "goal"
                    scores[actor] += 1
                else:
                    outcome = RNG.choice(["saved", "off_target", "blocked"])
                # Simplified: all shots lead to a new opposition possession.
                possession = opponent(before)
            elif kind in {"tackle", "interception"}:
                possession = actor
            elif kind == "foul":
                outcome = "committed"
                # Fouled team retains possession for a free kick.
                if RNG.random() < 0.22:
                    card = "yellow" if RNG.random() < 0.92 else "red"
                    cards[actor][card] += 1
            elif kind == "corner":
                outcome = "awarded"
                # Corner belongs to the attacking side; possession remains with them.

            event = {
                "event_id": f"evt_{event_id:04d}",
                "match_id": MATCH_ID,
                "minute": minute,
                "second": second,
                "timestamp_seconds": (minute - 1) * 60 + second,
                "team_id": actor,
                "player_id": f"{actor}_{RNG.randint(1, 11):02d}",
                "event_type": kind,
                "outcome": outcome,
                "x": x,
                "y": y,
                "xg": xg,
                "possession_team": before,
                "possession_id": possession_id,
                "card": card,
            }
            events.append(event)
            event_id += 1
            if possession != before:
                possession_id += 1

    return events


if __name__ == "__main__":
    events = generate_match()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as file:
        json.dump(events, file, indent=2)
    print(f"Generated {len(events)} events")
    print(f"Saved to {OUTPUT}")
