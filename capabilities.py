"""What the code under test can do, probed once for the whole run.

A branch where a feature is still missing marks the tests that need it
instead of failing them, so the same suite runs on every branch. Each
answer comes from the real code, never from a branch name.
"""

import json
import subprocess
import sys
import tempfile
from functools import cache
from pathlib import Path


def _written(name: str, text: str) -> str:
    """Returns the path of a new temporary file holding a text.

    name -- the file name, inside a folder of its own
    text -- what to write in it
    """

    path = Path(tempfile.mkdtemp()) / name
    path.write_text(text, encoding="utf-8")
    return str(path)


@cache
def clamps_a_bad_config_value() -> bool:
    """Returns whether a value the model refuses falls back to its default.

    The subject asks the game to carry on; a branch that still raises
    ConfigError instead has the tests of that behaviour marked.
    """

    from src import Config
    from src.config import ConfigError

    try:
        Config.ConfigModel.load_from_file(_written("lives.json",
                                                   '{"lives": -3}'))
    except ConfigError:
        return False
    return True


@cache
def reports_an_unreadable_config() -> bool:
    """Returns whether a path in no existing folder raises ConfigError."""

    from src import Config
    from src.config import ConfigError

    try:
        Config.ConfigModel.load_from_file("/nonexistent/pacman/config.json")
    except ConfigError:
        return True
    return False


@cache
def opens_a_next_stage() -> bool:
    """Returns whether a won level leads to another one."""

    from src import GameState

    return hasattr(GameState, "next_stage")


@cache
def drops_only_a_mistyped_score() -> bool:
    """Returns whether a row with a bad score leaves the other rows in place.

    The configuration is put back as it was, so collecting a test file
    never changes what the next one reads.
    """

    from src import Config
    from src.scores import load_scores

    table = _written("highscores.json", json.dumps([
        {"name": "Sannaka", "score": 1110},
        {"name": "foliole", "score": "twenty"}]))
    before = _written("before.json", json.dumps(Config.model_dump(
        mode="json")))
    try:
        Config.load_from_file(_written("config.json", json.dumps(
            {"highscore_filename": table})))
        return len(load_scores()) == 1
    finally:
        Config.load_from_file(before)


@cache
def reports_a_missing_video_device() -> bool:
    """Returns whether a machine with no screen raises instead of exiting.

    The renderer is built in a child process: a branch that still calls
    sys.exit would end the test run while this file is being collected.
    """

    probe: str = (
        "from manage_screen.renderer import PygameRenderer\n"
        "try:\n"
        "    PygameRenderer(100, 100, 'probe')\n"
        "except SystemExit:\n"
        "    raise SystemExit(2)\n"
        "except BaseException:\n"
        "    raise SystemExit(3)\n"
        "raise SystemExit(4)\n")
    run = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(Path(__file__).resolve().parent.parent),
        env={"SDL_VIDEODRIVER": "pacman-has-no-such-driver",
             "SDL_AUDIODRIVER": "dummy", "PATH": "/usr/bin:/bin",
             "PYGAME_HIDE_SUPPORT_PROMPT": "1"},
        capture_output=True, text=True, timeout=120)
    return run.returncode == 3


@cache
def has_a_cheat_tick() -> bool:
    """Returns whether the game state owns the length of a tick."""

    from src import GameState

    return hasattr(GameState, "tick_ms")


@cache
def speeds_up_when_cheating() -> bool:
    """Returns whether the cheat mode shortens a tick of the game.

    The mode is switched on to read the tick, then switched back off.
    """

    from src import GameState

    if not has_a_cheat_tick():
        return False
    vanilla: int = GameState.tick_ms
    GameState.cheat = True
    try:
        return GameState.tick_ms < vanilla
    finally:
        GameState.cheat = False


@cache
def keeps_scores_as_models() -> bool:
    """Returns whether a row of the leaderboard is a pydantic model."""

    from pydantic import BaseModel

    from src.scores import Score

    return isinstance(Score, type) and issubclass(Score, BaseModel)
