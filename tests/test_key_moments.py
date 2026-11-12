
import json
from pathlib import Path

from src.processing.key_moments import (
    detect_key_moments,
    identify_winning_goal,
)


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "synthetic"
    / "match_001.json"
)


def load_moments():
    with open(DATA_PATH, encoding="utf-8") as file:
        events = json.load(file)

    return identify_winning_goal(detect_key_moments(events))


def test_total_goals():
    moments = load_moments()

    assert len(moments) == 5


def test_goal_minutes():
    moments = load_moments()

    assert [moment["minute"] for moment in moments] == [
        18, 36, 57, 72, 86
    ]


def test_equalisers():
    moments = load_moments()

    equaliser_minutes = [
        moment["minute"]
        for moment in moments
        if moment["significance"] == "equaliser"
    ]

    assert equaliser_minutes == [36, 72]


def test_winning_goal():
    moments = load_moments()

    winners = [
        moment
        for moment in moments
        if moment.get("is_winning_goal")
    ]

    assert len(winners) == 1
    assert winners[0]["minute"] == 86
    assert winners[0]["player_name"] == "Erling Haaland"
