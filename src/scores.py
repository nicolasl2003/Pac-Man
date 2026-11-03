import json
import os
import sys
from . import Config
from contextlib import suppress
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class Score(BaseModel):
    """Represent one high-score entry with a player name and score.

    The name is cut down to ASCII letters, digits and spaces.
    """

    name: str = Field(min_length=1, max_length=10, strict=True)
    score: int = Field(ge=0, strict=True)

    @field_validator("name", mode="before")
    @classmethod
    def _sanitize_name(cls, name: Any) -> Any:
        """Cleans a name to be accepted by the highscore name convention.

        Args:
            name: The name to be sanitized, left as is when not a string

        Returns:
            The cleaned up name
        """
        if not isinstance(name, str):
            return name
        kept: str = "".join(char for char in name
                            if char.isascii()
                            and (char.isalnum() or char == " "))
        return kept[:Config.name_length] or "PLAYER"


def load_scores() -> list[Score]:
    """Read highscores from a JSON file.

    Returns:
        The ten best non-negative scores, sorted by score.
        An empty list if the file is missing or unreadable
    """

    if not os.path.isfile(Config.highscore_filename):
        return []
    try:
        with open(Config.highscore_filename, "r", encoding="utf-8") as file:
            data: Any = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print("[Highscores] "
              f"{Config.highscore_filename} ignored: {error}",
              file=sys.stderr)
        return []
    if not isinstance(data, list):
        return []
    scores: list[Score] = []
    for entry in data:
        with suppress(ValidationError):
            scores.append(Score.model_validate(entry))
    return sorted(scores, key=lambda s: s.score, reverse=True)[:10]


def save_score(name: str, score: int) -> None:
    """Add a score to the configured high-score JSON list.

    Only the ten best scores are kept, and a row the table refuses is
    ignored.

    Args:
        name: Player name to store, cut down to ASCII letters, digits and
            spaces within the configured length.
        score: Number of points earned.
    """
    try:
        row: Score = Score(name=name, score=score)
    except ValidationError as error:
        print(f"[Highscores] {score} not saved: {error.errors()[0]['msg']}",
              file=sys.stderr)
        return
    scores: list[Score] = load_scores()
    scores.append(row)
    scores.sort(key=lambda s: s.score, reverse=True)
    try:
        with open(Config.highscore_filename, "w", encoding="utf-8") as file:
            json.dump([s.model_dump() for s in scores[:10]], file, indent=4)
    except OSError as error:
        print("[Highscores] "
              f"could not save to {Config.highscore_filename}: {error}",
              file=sys.stderr)
