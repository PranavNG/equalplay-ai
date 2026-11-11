
import json
from pathlib import Path

from src.processing.key_moments import (
    detect_key_moments,
    identify_winning_goal
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"


def build_match_context():
    with open(DATA_DIR / "match_001_metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)

    with open(DATA_DIR / "match_001_stats.json", encoding="utf-8") as f:
        stats = json.load(f)

    with open(DATA_DIR / "match_001.json", encoding="utf-8") as f:
        events = json.load(f)

    moments = identify_winning_goal(detect_key_moments(events))

    context = {
        "match_id": "match_001",
        "competition": metadata["competition"],
        "teams": {
            "HOME": metadata["teams"]["HOME"]["name"],
            "AWAY": metadata["teams"]["AWAY"]["name"]
        },
        "final_score": {
            "HOME": stats["HOME"]["goals"],
            "AWAY": stats["AWAY"]["goals"]
        },
        "statistics": {
            "HOME": stats["HOME"],
            "AWAY": stats["AWAY"]
        },
        "key_moments": moments,
        "is_synthetic": True
    }

    return context
