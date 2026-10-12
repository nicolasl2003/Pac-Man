import json
from .config import Config
from typing import TypedDict


class Score(TypedDict):
    """Represent one high-score entry with a player name and score."""
    name: str
    score: int


def load_scores(path: str | None = None) -> list[Score]:
    """Read highscores from a JSON file.

    Args:
        path: Path to the highscores JSON file, or None to use the
            configured path.

    Returns:
        The ten best non-negative scores, sorted by score descending.
        Returns an empty list if the file is missing or invalid.
    """
    if path is None:
        path = Config.highscore_filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        scores: list[Score] = [
            {"name": str(entry["name"]), "score": int(entry["score"])}
            for entry in data
            if isinstance(entry, dict) and "name" in entry and "score" in entry
            and int(entry["score"]) >= 0
        ]
    except (FileNotFoundError,
            json.JSONDecodeError, KeyError, TypeError, ValueError):
        return []
    return sorted(scores, key=lambda s: s["score"], reverse=True)[:10]


def save_score(name: str, score: int, filepath: str | None = None) -> None:
    """Add a score to the configured high-score JSON list.

    Only the ten best scores are kept, and a negative score is ignored.

    Args:
        name: Player name to store, cut down to ASCII letters, digits and
            spaces within the configured length.
        score: Number of points earned.
        filepath: Destination path, or None to use the configured path.
    """
    if score < 0:
        return
    if filepath is None:
        filepath = Config.highscore_filename
    safe_name = "".join(
        char for char in name
        if char.isascii() and (char.isalnum() or char == " ")
    )[:Config.name_length] or "PLAYER"
    scores: list[Score] = load_scores(filepath)
    scores.append({"name": safe_name, "score": score})
    scores.sort(key=lambda s: s["score"], reverse=True)
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(scores[:10], file, indent=4)
