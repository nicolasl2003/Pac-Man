import os
from .config import Config


def load_scores(filepath: str | None = None) -> list[tuple[str, int]]:
    if filepath is None:
        filepath = Config.highscore_filename
    if (not os.path.exists(filepath)):
        return ([])

    scores: list[tuple[str, int]] = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split()
            if (len(parts) != 2):
                continue
            name, score_str = parts
            if (not score_str.isdigit()):
                continue
            scores.append((name, int(score_str)))
        scores.sort(key=lambda pair: pair[1], reverse=True)
    return (scores)


def save_score(name: str, score: int, filepath: str | None = None) -> None:
    if filepath is None:
        filepath = Config.highscore_filename
    safe_name = name.replace(" ", "_") or "PLAYER"
    with open(filepath, "a", encoding="utf-8") as file:
        file.write(f"{safe_name} {score}\n")
