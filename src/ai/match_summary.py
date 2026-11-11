
import json
from pathlib import Path
from functools import lru_cache
from src.ai.azure_client import generate_response

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"


@lru_cache(maxsize=32)
def generate_match_summary():
    with open(DATA_DIR / "match_001_metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)

    with open(DATA_DIR / "match_001_stats.json", encoding="utf-8") as f:
        stats = json.load(f)

    with open(DATA_DIR / "match_001.json", encoding="utf-8") as f:
        events = json.load(f)

    key_events = [
        {
            "minute": event["minute"],
            "team": metadata["teams"][event["team_id"]]["name"],
            "player": event.get("player_name"),
            "event_type": event["event_type"],
            "outcome": event["outcome"],
            "xg": event.get("xg"),
        }
        for event in events
        if event["event_type"] in {"shot", "yellow_card", "red_card"}
    ]

    match_context = {
        "competition": metadata["competition"],
        "home_team": metadata["teams"]["HOME"]["name"],
        "away_team": metadata["teams"]["AWAY"]["name"],
        "home_stats": stats["HOME"],
        "away_stats": stats["AWAY"],
        "key_events": key_events,
    }

    prompt = f"""
You are a professional association football (soccer) commentator.

Write an engaging match recap of approximately 150-200 words.

Requirements:
- Use only the provided synthetic match data.
- Clearly describe the final score and goalscorers.
- Explain important turning points in chronological order.
- Use match statistics to support your analysis.
- Write naturally, like a football journalist.
- You may offer reasonable interpretations of the statistics.
- Do not invent events, assists, injuries, or tactical changes.
- Do not present this fictional match as a real result.

Match data:
{json.dumps(match_context, indent=2)}
"""

    return generate_response(prompt)


if __name__ == "__main__":
    print(generate_match_summary())
