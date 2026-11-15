"""Accessible commentary for every synthetic match event, with resumable disk caching."""
import hashlib
import json
import logging
import os
import re
from pathlib import Path

from src.ai.azure_client import generate_response

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "synthetic"
CACHE_FILE = DATA_DIR / "match_001_commentary_cache.json"
MATCH_ID = "match_001"
VERSION = 3
BATCH_SIZE = 6
LOG = logging.getLogger(__name__)


def _load(filename):
    with (DATA_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


def _event_time(event):
    timestamp = event.get("timestamp_seconds")
    if timestamp is None:
        timestamp = event.get("minute", 0) * 60 + event.get("second", 0)
    return (float(timestamp), str(event.get("event_id", "")))


def _build_highlights():
    events = sorted(_load("match_001.json"), key=_event_time)
    metadata = _load("match_001_metadata.json")
    teams = {side: metadata["teams"][side]["name"] for side in ("HOME", "AWAY")}
    score = {"HOME": 0, "AWAY": 0}
    highlights = []
    for event in events:
        side = event.get("team_id")
        kind = event.get("event_type")
        outcome = event.get("outcome")
        if kind == "shot" and outcome == "goal" and side in score:
            score[side] += 1
        # Preserve ALL events, even when the team is absent or unknown.
        highlights.append({
            "event_id": str(event["event_id"]),
            "minute": event.get("minute", 0),
            "timestamp_seconds": _event_time(event)[0],
            "team": teams.get(side, str(side or "Unknown team")),
            "player": event.get("player_name"),
            "event_type": kind,
            "outcome": outcome,
            "score_after": dict(score),
        })
    ids = [e["event_id"] for e in highlights]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate event_id values in match data")
    return highlights


def _fallback(event):
    player = event["player"] or "A player"
    team = event["team"]
    kind, outcome = event["event_type"], event["outcome"]
    score = event["score_after"]
    scoreline = f"{score['HOME']}–{score['AWAY']}"
    if kind == "shot" and outcome == "goal":
        return (f"GOAL! {player} scores for {team}! It's {scoreline}!",
                f"{player} scores for {team}. The score is {scoreline}.")
    if kind == "shot":
        endings = {"saved": "is saved", "blocked": "is blocked", "off_target": "goes off target"}
        ending = endings.get(outcome, "does not result in a goal")
        return (f"{player} shoots for {team}. The attempt {ending}.",
                f"{player} takes a shot for {team}. It {ending}.")
    if kind == "pass":
        result = "completes a pass" if outcome == "successful" else "attempts a pass"
        return (f"{player} {result} for {team}.", f"{player} {result} for {team}.")
    if kind == "tackle":
        return (f"{player} makes a tackle for {team}.", f"{player} makes a tackle for {team}.")
    if kind == "interception":
        return (f"{player} intercepts for {team}.", f"{player} makes an interception for {team}.")
    if kind == "foul":
        return (f"A foul involving {player} of {team}.", f"A foul involving {team}.")
    if kind == "corner":
        return (f"Corner to {team}.", f"{team} has a corner.")
    if kind in {"yellow_card", "red_card"}:
        card = "red" if kind == "red_card" else "yellow"
        return (f"A {card} card for {team}.", f"A {team} player receives a {card} card.")
    return (f"{team}: {str(kind or 'match event').replace('_', ' ')}.",
            f"{team}: {str(kind or 'match event').replace('_', ' ')}.")


def _extract_json(text):
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    return json.loads(clean)


def _fingerprint(highlights):
    raw = json.dumps({"version": VERSION, "highlights": highlights}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate(items, originals):
    if not isinstance(items, list) or len(items) != len(originals):
        raise ValueError("Incorrect event count")
    output = []
    for original, item in zip(originals, items):
        if not isinstance(item, dict) or str(item.get("event_id")) != original["event_id"]:
            raise ValueError("Event IDs do not match")
        expressive, simplified = item.get("expressive"), item.get("simplified")
        if not all(isinstance(v, str) and 0 < len(v.strip()) <= 400 for v in (expressive, simplified)):
            raise ValueError("Invalid commentary text")
        output.append({"event_id": original["event_id"], "minute": original["minute"],
                       "expressive": expressive.strip(), "simplified": simplified.strip()})
    return output


def _save_cache(fingerprint, results):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"match_id": MATCH_ID, "version": VERSION,
               "fingerprint": fingerprint, "highlights": results}
    temp_file = CACHE_FILE.with_suffix(".json.tmp")
    temp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp_file, CACHE_FILE)


def _cached_prefix(highlights, fingerprint):
    if not CACHE_FILE.exists():
        return []
    try:
        cached = _load(CACHE_FILE.name)
        if cached.get("fingerprint") != fingerprint or cached.get("version") != VERSION:
            return []
        saved = cached.get("highlights", [])
        if not isinstance(saved, list) or len(saved) > len(highlights):
            return []
        return _validate(saved, highlights[:len(saved)])
    except (OSError, ValueError, KeyError, TypeError):
        LOG.warning("Invalid commentary cache; starting fresh")
        return []


def _generate_batch(batch):
    prompt = """Write accessible commentary for a FICTIONAL football match.
Return ONLY JSON: {"highlights": [{"event_id": "...", "expressive": "...", "simplified": "..."}]}.
Exactly one result per event, same order and IDs.
Expressive: one or two lively, natural sentences (max 35 words). Vary phrasing.
Simplified: one clear factual sentence (max 22 words).
For routine passes and tackles, be brief. Do not repeat the score for routine events.
For goals, be energetic, especially a late goal that changes the lead. Scores use HOME–AWAY order
with an en dash (e.g. 2–3). Mention only facts known at that event; never anticipate the result.
Do not invent shot techniques, assists, player reactions, tactics, stadium atmosphere or footage.
Do not infer a winning goal solely because it occurs late. Use only event facts supplied.
Events:\n""" + json.dumps(batch, ensure_ascii=False)
    raw = _extract_json(generate_response(prompt))
    return _validate(raw["highlights"], batch)


def generate_match_commentary():
    """Return all events. Set EQUALPLAY_COMMENTARY_MODE=fallback to test without AI calls."""
    highlights = _build_highlights()
    if not highlights:
        return {"match_id": MATCH_ID, "source": "fallback", "highlights": []}

    # Explicit test mode does not read, overwrite or generate the AI cache.
    if os.getenv("EQUALPLAY_COMMENTARY_MODE", "").lower() == "fallback":
        return {"match_id": MATCH_ID, "source": "fallback_test", "highlights": [
            {"event_id": e["event_id"], "minute": e["minute"],
             "expressive": _fallback(e)[0], "simplified": _fallback(e)[1]}
            for e in highlights]}

    fingerprint = _fingerprint(highlights)
    results = _cached_prefix(highlights, fingerprint)
    if len(results) == len(highlights):
        return {"match_id": MATCH_ID, "source": "saved_cache", "highlights": results}

    try:
        for start in range(len(results), len(highlights), BATCH_SIZE):
            batch = highlights[start:start + BATCH_SIZE]
            results.extend(_generate_batch(batch))
            _save_cache(fingerprint, results)  # checkpoint each successful batch
        return {"match_id": MATCH_ID, "source": "azure_openai", "highlights": results}
    except Exception:
        LOG.exception("AI commentary interrupted; completed batches are cached")
        remaining = highlights[len(results):]
        fallback = [{"event_id": e["event_id"], "minute": e["minute"],
                     "expressive": _fallback(e)[0], "simplified": _fallback(e)[1]}
                    for e in remaining]
        return {"match_id": MATCH_ID, "source": "partial_fallback", "highlights": results + fallback}
