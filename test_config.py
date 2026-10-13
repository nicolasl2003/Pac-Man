"""The configuration file drives the game and never crashes it."""

import json
import os
from pathlib import Path
from typing import Callable

import pytest

from src import Config, GameState
from src.config import ConfigError


def test_defaults_are_readable_without_any_file() -> None:
    """A fresh Config answers with usable values."""

    assert Config.lives >= 1
    assert Config.ghost_count >= 0
    assert isinstance(Config.highscore_filename, str)


def test_loaded_values_replace_the_defaults(
        write_config: Callable[[str], str]) -> None:
    """Keys present in the file win over the defaults."""

    Config.load_from_file(write_config('{"lives": 7, "ghost_count": 2}'))

    assert Config.lives == 7
    assert Config.ghost_count == 2


def test_comment_lines_are_ignored(
        write_config: Callable[[str], str]) -> None:
    """Lines starting with # are stripped before parsing."""

    Config.load_from_file(write_config(
        '# the lives of the player\n{\n"lives": 5\n# trailing note\n}\n'))

    assert Config.lives == 5


def test_unknown_keys_are_ignored(
        write_config: Callable[[str], str]) -> None:
    """A key the game does not know does not stop the load."""

    Config.load_from_file(write_config('{"lives": 4, "nonsense": 12}'))

    assert Config.lives == 4
    assert not hasattr(Config, "nonsense")


def test_an_out_of_range_value_is_reported(
        write_config: Callable[[str], str]) -> None:
    """A negative count raises ConfigError, not ValidationError."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('{"lives": -3}'))


def test_a_mistyped_value_is_reported(
        write_config: Callable[[str], str]) -> None:
    """A string where an int belongs raises ConfigError."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('{"ghost_count": "four"}'))


def test_a_missing_file_is_written_from_the_defaults(
        tmp_path: Path) -> None:
    """A first run gets a template to edit instead of an error."""

    path = tmp_path / "absent.json"

    Config.load_from_file(str(path))

    assert Config.lives >= 1
    assert path.exists()


def test_the_written_template_loads_again(tmp_path: Path) -> None:
    """The template the game writes is a file the game can read."""

    path = tmp_path / "absent.json"
    Config.load_from_file(str(path))
    written = json.loads(path.read_text())

    Config.load_from_file(str(path))

    assert written["ghost_spawn"] == Config.ghost_spawn.value
    assert written["ghost_chase"] == Config.ghost_chase.value
    assert json.loads(path.read_text()) == written


def test_an_unwritable_template_path_is_not_fatal() -> None:
    """A folder the game cannot write to still leaves it configured."""

    Config.load_from_file("/nonexistent/pacman/config.json")

    assert Config.lives >= 1


def test_a_broken_file_is_reported(
        write_config: Callable[[str], str]) -> None:
    """Invalid JSON raises ConfigError, not JSONDecodeError."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('{"lives": }'))


def test_a_failed_load_leaves_the_previous_values(
        write_config: Callable[[str], str]) -> None:
    """A broken file never leaves the game half configured."""

    Config.load_from_file(write_config('{"lives": 6}'))
    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('{"lives": }'))

    assert Config.lives == 6


def test_loading_reaches_the_modules_that_imported_config(
        write_config: Callable[[str], str]) -> None:
    """Every module shares one Config object, so a load is seen by all."""

    import src.maze

    Config.load_from_file(write_config('{"lives": 9}'))

    assert getattr(src.maze, "Config").lives == 9


def test_a_new_run_uses_the_loaded_values(
        write_config: Callable[[str], str]) -> None:
    """Resetting the game applies the configured lives and ghosts."""

    Config.load_from_file(write_config('{"lives": 6, "ghost_count": 3}'))
    GameState.reset()

    assert GameState.lives == 6
    assert len(GameState.level.ghosts) == 3


def test_a_new_run_uses_the_loaded_timer(
        write_config: Callable[[str], str]) -> None:
    """The level time of the config is what a new run starts with."""

    Config.load_from_file(write_config('{"level_time": 123}'))
    GameState.reset()

    assert GameState.timer == Config.to_ticks(123)


def test_seconds_are_converted_into_ticks() -> None:
    """At 20 ticks a second, two seconds last forty ticks."""

    assert Config.to_ticks(2) == 40


def test_a_new_run_keeps_the_session_highscore() -> None:
    """The highscore outlives a run, the score does not."""

    GameState.score = 120
    GameState.highscore = 1234
    GameState.reset()

    assert GameState.highscore == 1234
    assert GameState.score == 0


def test_a_directory_is_reported(tmp_path: Path) -> None:
    """Pointing at a folder raises ConfigError, not IsADirectoryError."""

    with pytest.raises(ConfigError):
        Config.load_from_file(str(tmp_path))


def test_an_empty_file_is_reported(
        write_config: Callable[[str], str]) -> None:
    """A file with nothing to read is not valid JSON."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config(""))


def test_a_file_of_comments_only_gives_the_defaults(
        write_config: Callable[[str], str]) -> None:
    """Stripping every line leaves an empty configuration, not an error."""

    Config.load_from_file(write_config("# nothing\n# but notes\n"))

    assert Config.lives >= 1


def test_a_json_list_is_reported(
        write_config: Callable[[str], str]) -> None:
    """The config file must hold an object, not an array."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('[1, 2, 3]'))


def test_a_json_scalar_is_reported(
        write_config: Callable[[str], str]) -> None:
    """A bare number is not a configuration either."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('42'))


def test_non_utf8_bytes_are_reported(tmp_path: Path) -> None:
    """A binary file raises ConfigError, not UnicodeDecodeError."""

    path = tmp_path / "binary.json"
    path.write_bytes(b'{"lives": 3}\xff\xfe')

    with pytest.raises(ConfigError):
        Config.load_from_file(str(path))


def test_an_unreadable_file_is_reported(tmp_path: Path) -> None:
    """A file without read permission raises ConfigError."""

    path = tmp_path / "locked.json"
    path.write_text('{"lives": 3}')
    path.chmod(0o000)
    if os.access(str(path), os.R_OK):
        pytest.skip("running as root, permissions are not enforced")

    try:
        with pytest.raises(ConfigError):
            Config.load_from_file(str(path))
    finally:
        path.chmod(0o644)


def test_loading_does_not_leak_file_handles(
        write_config: Callable[[str], str],
        tmp_path: Path) -> None:
    """Every load closes its file, even the ones that fail."""

    if not Path("/proc/self/fd").exists():
        pytest.skip("no /proc on this platform")
    good = write_config('{"lives": 3}')
    broken = str(tmp_path / "broken.json")
    Path(broken).write_text('{"lives": }')
    opened = len(os.listdir("/proc/self/fd"))

    for _ in range(50):
        Config.load_from_file(good)
        with pytest.raises(ConfigError):
            Config.load_from_file(broken)

    assert len(os.listdir("/proc/self/fd")) <= opened + 1


def test_the_name_length_limit_is_configurable(
        write_config: Callable[[str], str]) -> None:
    """The leaderboard name limit comes from the config."""

    Config.load_from_file(write_config('{"name_length": 4}'))

    assert Config.name_length == 4


def test_the_frame_and_tick_rates_are_configured() -> None:
    """The game draws several frames for each logic tick."""

    assert 60 <= Config.framerate <= 80
    assert Config.frame_per_tick >= 1
    assert Config.framerate >= Config.frame_per_tick


def test_the_game_ticks_twenty_times_a_second() -> None:
    """Twenty ticks a second is the rate the gameplay was tuned for."""

    assert Config.framerate / Config.frame_per_tick == 20
