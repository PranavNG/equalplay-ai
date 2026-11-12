
import json
from pathlib import Path

from src.processing.match_stats import calculate_stats


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "synthetic"
    / "match_001.json"
)


def load_events():
    with open(DATA_PATH, encoding="utf-8") as file:
        return json.load(file)


def test_final_score():
    stats = calculate_stats(load_events())

    assert stats["HOME"]["goals"] == 2
    assert stats["AWAY"]["goals"] == 3


def test_shot_statistics():
    stats = calculate_stats(load_events())

    assert stats["HOME"]["shots"] == 7
    assert stats["AWAY"]["shots"] == 9

    assert stats["HOME"]["shots_on_target"] == 3
    assert stats["AWAY"]["shots_on_target"] == 5


def test_possession_totals():
    stats = calculate_stats(load_events())

    total = (
        stats["HOME"]["possession"]
        + stats["AWAY"]["possession"]
    )

    assert abs(total - 100) < 0.1
