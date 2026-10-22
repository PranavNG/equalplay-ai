
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from src.processing.match_stats import calculate_stats

# Resolve paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"

app = FastAPI(
    title="EqualPlay AI",
    description="Explainable synthetic football match intelligence API",
    version="0.1.0"
)

# Allow the React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"]
)


def load_json(filename: str):
    """Load a synthetic football data file."""
    file_path = DATA_DIR / filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Data file not found: {filename}"
        )

    try:
        with file_path.open(encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON data: {filename}"
        )


@app.get("/")
def home():
    return {
        "application": "EqualPlay AI",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/api/match")
def get_match():
    """Return match metadata and team names."""
    return load_json("match_001_metadata.json")


@app.get("/api/stats")
def get_stats():
    """Return calculated match statistics."""
    return load_json("match_001_stats.json")


@app.get("/api/events")
def get_events():
    """Return chronological synthetic match events."""
    events = load_json("match_001.json")

    return sorted(
        events,
        key=lambda event: (
            event.get("timestamp_seconds",
                      (event["minute"] - 1) * 60
                      + event["second"]),
            event["event_id"]
        )
    )


@app.get("/api/replay")
def get_replay(minute: int = Query(default=0, ge=0, le=90)):
    """
    Return the match state at a particular minute.
    Example: /api/replay?minute=45
    """
    events = load_json("match_001.json")
    metadata = load_json("match_001_metadata.json")

    # Only include events that have happened by this minute
    elapsed_events = [
        event for event in events
        if event["minute"] <= minute
    ]

    # Recalculate statistics using only elapsed events
    stats = calculate_stats(elapsed_events)

    # Calculate the score from goal events
    score = {"HOME": 0, "AWAY": 0}

    for event in elapsed_events:
        if (
            event["event_type"] == "shot"
            and event["outcome"] == "goal"
        ):
            score[event["team_id"]] += 1

    # Collect important events for the timeline
    important_types = {
        "shot", "corner", "yellow_card", "red_card"
    }

    key_events = [
        event for event in elapsed_events
        if event["event_type"] in important_types
    ]

    return {
        "match_id": "match_001",
        "minute": minute,
        "teams": metadata["teams"],
        "score": score,
        "stats": stats,
        "key_events": key_events,
        "events_processed": len(elapsed_events)
    }
