"""Shared fixtures resetting the globals around every test."""

import json
import os
import sys
from pathlib import Path
from typing import (TYPE_CHECKING, Any, Callable, Generator, Iterator,
                    Optional)

import pytest

from isolation import IsolatedModule
from review import Review, Site, crash_site, declared_site

if TYPE_CHECKING:
    from src import Level

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))


def pytest_configure(config: pytest.Config) -> None:
    """Registers the suite's marker and lets a broken file be stepped over.

    config -- the settings of the pytest run
    """

    config.option.continue_on_collection_errors = True
    config.addinivalue_line(
        "markers", "verifies(target): the code of the game a test covers")


def pytest_pycollect_makemodule(module_path: Path,
                                parent: pytest.Collector) -> pytest.Module:
    """Collects every test file so a broken import only fails its own tests.

    module_path -- the test file to collect
    parent -- the collector of the folder holding it
    """

    return IsolatedModule.from_parent(parent, path=module_path)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
        item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Writes on a report where its failure is to be reported.

    The site is read while the traceback of the failure is still at hand.
    item -- the test the report is about
    call -- the phase of the test the report is about
    """

    report: pytest.TestReport = yield
    if report.outcome != "passed" or hasattr(report, "wasxfail"):
        site: Optional[Site] = (declared_site(item)
                                or crash_site(call.excinfo))
        if site is not None:
            setattr(report, "review_site", site)
    return report


def _gaps(terminalreporter: Any) -> dict[str, list[Any]]:
    """Returns the tests each gap of the run held back.

    terminalreporter -- the plugin holding what the run produced
    """

    found: dict[str, list[Any]] = {}
    for report in terminalreporter.stats.get("xfailed", []):
        reason: str = str(getattr(report, "wasxfail", "")) or "no reason given"
        found.setdefault(reason, []).append(report)
    return found


def pytest_terminal_summary(terminalreporter: Any) -> None:
    """Reports what the run found, failure by failure and gap by gap.

    A failure is reported on the code it covers, while a gap only warns:
    a branch where a feature is still missing ends on a green run.
    terminalreporter -- the plugin holding what the run produced
    """

    review: Review = Review()
    for outcome in ("failed", "error"):
        for report in terminalreporter.stats.get(outcome, []):
            review.failure(report, outcome)
    gaps: dict[str, list[Any]] = _gaps(terminalreporter)
    if gaps:
        terminalreporter.write_sep("-", "gaps the suite stepped around")
    for gap, reports in sorted(gaps.items()):
        terminalreporter.write_line(f"{len(reports)} test(s) not run: {gap}")
        review.gap(gap, reports)
    review.close()


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
