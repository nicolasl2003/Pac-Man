import json
from .config import Config
from typing import TypedDict


class Score(TypedDict):
    """A single highscore entry."""
    name: str
    score: int


def load_scores(path: str = "highscores.json") -> list[Score]:
    """Read highscores from a JSON file.

    Args:
        path: Path to the highscores JSON file.

    Returns:
        A list of scores sorted by score descending.
        Returns an empty list if the file is missing or invalid.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        scores: list[Score] = [
            {"name": str(entry["name"]), "score": int(entry["score"])}
            for entry in data
            if isinstance(entry, dict) and "name" in entry and "score" in entry
        ]
    except (FileNotFoundError,
            json.JSONDecodeError, KeyError, TypeError, ValueError):
        return []
    return sorted(scores, key=lambda s: s["score"], reverse=True)


def save_score(name: str, score: int, filepath: str | None = None) -> None:
    if filepath is None:
        filepath = Config.highscore_filename
    safe_name = name.replace(" ", "_") or "PLAYER"
    with open(filepath, "a", encoding="utf-8") as file:
        file.write(f"{safe_name} {score}\n")
