
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
        "http://127.0.0.1:5173"
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
