"""Shared fixtures resetting the globals around every test."""

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator

import pytest

from isolation import IsolatedModule

if TYPE_CHECKING:
    from src import Level

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def pytest_configure(config: pytest.Config) -> None:
    """Runs the other test files when one of them cannot be collected.

    config -- the settings of the pytest run
    """

    config.option.continue_on_collection_errors = True


def pytest_pycollect_makemodule(module_path: Path,
                                parent: pytest.Collector) -> pytest.Module:
    """Collects every test file so a broken import only fails its own tests.

    module_path -- the test file to collect
    parent -- the collector of the folder holding it
    """

    return IsolatedModule.from_parent(parent, path=module_path)


@pytest.fixture(autouse=True)
def fresh_state(tmp_path: Path,
                monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Puts the globals back to their defaults around each test.

    The test runs from its own temporary folder and the score file is sent
    there too, so a test never writes into the repository, even when a
    config it loads leaves the score path at its relative default. Every
    key is written, so the load reports none of them missing.
    """

    from src import Config, GameState

    monkeypatch.chdir(tmp_path)
    defaults = tmp_path / "defaults.json"
    values: dict[str, Any] = Config.ConfigModel().model_dump(mode="json")
    values["highscore_filename"] = str(tmp_path / "highscores.json")
    defaults.write_text(json.dumps(values))
    GameState.highscore = 0
    Config.load_from_file(str(defaults))
    GameState.reset()
    yield
    GameState.highscore = 0
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


CONFIG_VARIANTS: dict[str, dict[str, object]] = {
    "defaults": {},
    "random_ghosts": {"ghost_chase": "Random"},
    "hardcore_ghosts": {"ghost_chase": "Hardcore"},
    "one_ghost_one_life": {"ghost_count": 1, "lives": 1},
    "many_ghosts": {"ghost_count": 8},
    "few_pacgums": {"pacgum_count": 10, "super_pacgum_count": 2},
    "other_prizes": {"pacgum_points": 10, "ss_pacgum_points": 50,
                     "ghost_points": 200},
}


@pytest.fixture(params=list(CONFIG_VARIANTS))
def config_variant(request: pytest.FixtureRequest,
                   tmp_path: Path) -> str:
    """Runs the test once for each variation of the default config.

    Every variant keeps the default value of the keys it does not name.
    Returns the name of the variant
    """

    from src import Config, GameState

    path = tmp_path / "variant.json"
    values: dict[str, Any] = Config.ConfigModel().model_dump(mode="json")
    values["highscore_filename"] = str(tmp_path / "highscores.json")
    values.update(CONFIG_VARIANTS[request.param])
    path.write_text(json.dumps(values))
    Config.load_from_file(str(path))
    GameState.reset()
    return str(request.param)


@pytest.fixture
def write_scores(tmp_path: Path) -> Callable[[str], str]:
    """Returns a helper writing a score file and giving back its path."""

    def _write(content: str) -> str:
        path = tmp_path / "highscores.json"
        path.write_text(content)
        return str(path)

    return _write


@pytest.fixture
def open_level() -> Callable[..., "Level"]:
    """Returns a helper building a level on a maze without inner walls.

    The level is installed on GameState, since the entities read their
    maze from there.
    """

    from src import GameState, Level, Maze

    from helpers import open_grid

    def _build(width: int = 15, height: int = 15) -> Level:
        level = Level(Maze(open_grid(width, height)))
        GameState.level = level
        return level

    return _build
