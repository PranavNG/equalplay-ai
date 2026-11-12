
import json
from copy import deepcopy
from pathlib import Path

from src.processing.validate_events import validate_events


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "synthetic"
    / "match_001.json"
)


def load_events():
    with open(DATA_PATH, encoding="utf-8") as file:
        return json.load(file)


def test_valid_match_data():
    assert validate_events(load_events()) == []


def test_invalid_json_structure():
    errors = validate_events({"events": []})

    assert "Events must be a JSON array" in errors


def test_missing_required_field():
    events = deepcopy(load_events()[:1])
    del events[0]["event_id"]

    errors = validate_events(events)

    assert any("missing" in error for error in errors)


def test_duplicate_event_id():
    events = deepcopy(load_events()[:2])
    events[1]["event_id"] = events[0]["event_id"]

    errors = validate_events(events)

    assert any("Duplicate event ID" in error for error in errors)


def test_invalid_coordinates():
    events = deepcopy(load_events()[:1])
    events[0]["x"] = 150

    errors = validate_events(events)

    assert any("invalid x" in error for error in errors)


def test_invalid_event_type():
    events = deepcopy(load_events()[:1])
    events[0]["event_type"] = "unknown"

    errors = validate_events(events)

    assert any("invalid event type" in error for error in errors)


def test_invalid_timestamp():
    events = deepcopy(load_events()[:1])
    events[0]["timestamp_seconds"] = -10

    errors = validate_events(events)

    assert any("invalid timestamp_seconds" in error for error in errors)


def test_invalid_shot_xg():
    events = deepcopy(load_events())
    shot = next(event for event in events if event["event_type"] == "shot")
    shot["xg"] = 1.5

    errors = validate_events(events)

    assert any("invalid shot xG" in error for error in errors)
