"""Shared fixtures resetting the globals around every test."""

import json
import os
import sys
from pathlib import Path
from typing import Callable, Iterator

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import GameState, Level, Maze  # noqa: E402

from helpers import open_grid  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_state(tmp_path: Path) -> Iterator[None]:
    """Puts the globals back to their defaults around each test.

    The score file is sent to a temporary path, so a test never writes
    the one kept in the repository.
    """

    from src import Config

    defaults = tmp_path / "defaults.json"
    defaults.write_text(json.dumps(
        {"highscore_filename": str(tmp_path / "highscores.json")}))
    Config.load_from_file(str(defaults))
    GameState.reset()
    yield
    Config.load_from_file(str(defaults))
    GameState.reset()


@pytest.fixture
def write_config(tmp_path: Path) -> Callable[[str], str]:
    """Returns a helper writing a config file and giving back its path."""

    def _write(content: str) -> str:
        path = tmp_path / "config.json"
        path.write_text(content)
        return str(path)

    return _write


@pytest.fixture
def write_scores(tmp_path: Path) -> Callable[[str], str]:
    """Returns a helper writing a score file and giving back its path."""

    def _write(content: str) -> str:
        path = tmp_path / "highscores.json"
        path.write_text(content)
        return str(path)

    return _write


@pytest.fixture
def open_level() -> Callable[..., Level]:
    """Returns a helper building a level on a maze without inner walls.

    The level is installed on GameState, since the entities read their
    maze from there.
    """

    def _build(width: int = 15, height: int = 15) -> Level:
        level = Level(Maze(open_grid(width, height)))
        GameState.level = level
        return level

    return _build
