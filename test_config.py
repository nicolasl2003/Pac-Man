"""The configuration file drives the game and never crashes it."""

import json
import os
from pathlib import Path
from typing import Callable

import pytest

from src import Config, GameState
from src.config import ConfigError

from capabilities import (clamps_a_bad_config_value,
                          reports_an_unreadable_config)
from gaps import missing
from review import verifies


@verifies("src.config.ConfigWrapper.ConfigModel")
def test_defaults_are_readable_without_any_file() -> None:
    """A fresh Config answers with usable values."""

    assert Config.lives >= 1
    assert Config.ghost_count >= 0
    assert isinstance(Config.highscore_filename, str)


@verifies("src.config.ConfigWrapper.load_from_file")
def test_loaded_values_replace_the_defaults(
        write_config: Callable[[str], str]) -> None:
    """Keys present in the file win over the defaults."""

    Config.load_from_file(write_config('{"lives": 7, "ghost_count": 2}'))

    assert Config.lives == 7
    assert Config.ghost_count == 2


@verifies("src.config.ConfigWrapper.load_from_file")
def test_comment_lines_are_ignored(
        write_config: Callable[[str], str]) -> None:
    """Lines starting with # are stripped before parsing."""

    Config.load_from_file(write_config(
        '# the lives of the player\n{\n"lives": 5\n# trailing note\n}\n'))

    assert Config.lives == 5


@verifies("src.config.ConfigWrapper.load_from_file")
def test_unknown_keys_are_ignored(
        write_config: Callable[[str], str]) -> None:
    """A key the game does not know does not stop the load."""

    Config.load_from_file(write_config('{"lives": 4, "nonsense": 12}'))

    assert Config.lives == 4
    assert not hasattr(Config, "nonsense")


@missing("a config that carries on with a value out of range",
         when=not clamps_a_bad_config_value(), raises=ConfigError)
@verifies("src.config.ConfigWrapper.load_from_file")
def test_an_out_of_range_value_does_not_stop_the_game(
        write_config: Callable[[str], str],
        capsys: pytest.CaptureFixture[str]) -> None:
    """The subject asks to carry on with a safe value, and to say so."""

    Config.load_from_file(write_config('{"lives": -3}'))

    assert Config.lives >= 1
    assert capsys.readouterr().err


@missing("a config that carries on with a mistyped value",
         when=not clamps_a_bad_config_value(), raises=ConfigError)
@verifies("src.config.ConfigWrapper.load_from_file")
def test_a_mistyped_value_does_not_stop_the_game(
        write_config: Callable[[str], str],
        capsys: pytest.CaptureFixture[str]) -> None:
    """A string where an int belongs is replaced, and reported."""

    Config.load_from_file(write_config('{"ghost_count": "four"}'))

    assert isinstance(Config.ghost_count, int) and Config.ghost_count >= 0
    assert capsys.readouterr().err


@verifies("src.config.ConfigWrapper.load_from_file")
def test_a_missing_file_is_written_with_the_defaults(
        tmp_path: Path) -> None:
    """A path with no file gets a template, and the defaults are loaded."""

    path = tmp_path / "absent.json"

    Config.load_from_file(str(path))
    written = json.loads(path.read_text())

    assert written["lives"] == Config.lives
    assert set(written) == set(Config.ConfigModel.model_fields)


@missing("an error when the config path cannot be read",
         when=not reports_an_unreadable_config(),
         raises=pytest.fail.Exception)
@verifies("src.config.ConfigWrapper.load_from_file")
def test_an_unreachable_path_is_reported() -> None:
    """A path in no existing folder is an error, not a silent default."""

    with pytest.raises(ConfigError):
        Config.load_from_file("/nonexistent/pacman/config.json")


@verifies("src.config.ConfigWrapper.load_from_file")
def test_a_broken_file_is_reported(
        write_config: Callable[[str], str]) -> None:
    """Invalid JSON raises ConfigError, not JSONDecodeError."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('{"lives": }'))


@verifies("src.config.ConfigWrapper.load_from_file")
def test_a_failed_load_leaves_the_previous_values(
        write_config: Callable[[str], str]) -> None:
    """A broken file never leaves the game half configured."""

    Config.load_from_file(write_config('{"lives": 6}'))
    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('{"lives": }'))

    assert Config.lives == 6


@verifies("src.config.ConfigWrapper.load_from_file")
def test_loading_reaches_the_modules_that_imported_config(
        write_config: Callable[[str], str]) -> None:
    """Every module shares one Config object, so a load is seen by all."""

    import src.maze

    Config.load_from_file(write_config('{"lives": 9}'))

    assert getattr(src.maze, "Config").lives == 9


@verifies("src.game_state.GameStateModel.reset")
def test_a_new_run_uses_the_loaded_values(
        write_config: Callable[[str], str]) -> None:
    """Resetting the game applies the configured lives and ghosts."""

    Config.load_from_file(write_config('{"lives": 6, "ghost_count": 3}'))
    GameState.reset()

    assert GameState.lives == 6
    assert len(GameState.level.ghosts) == 3


@verifies("src.game_state.GameStateModel.reset_timer")
def test_a_new_run_uses_the_loaded_timer(
        write_config: Callable[[str], str]) -> None:
    """The level time of the config is what a new run starts with."""

    Config.load_from_file(write_config('{"level_time": 123}'))
    GameState.reset()

    assert GameState.timer == 123 * 1000 // Config.ms_per_tick


@verifies("src.game_state.GameStateModel.reset")
def test_a_new_run_clears_the_score_but_not_the_highscore() -> None:
    """The highscore outlives a run, the score does not."""

    GameState.score = 120
    GameState.highscore = 1234
    GameState.reset()

    assert GameState.highscore == 1234
    assert GameState.score == 0


@verifies("src.config.ConfigWrapper.load_from_file")
def test_a_directory_is_reported(tmp_path: Path) -> None:
    """Pointing at a folder raises ConfigError, not IsADirectoryError."""

    with pytest.raises(ConfigError):
        Config.load_from_file(str(tmp_path))


@verifies("src.config.ConfigWrapper.load_from_file")
def test_an_empty_file_is_reported(
        write_config: Callable[[str], str]) -> None:
    """A file with nothing to read is not valid JSON."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config(""))


@verifies("src.config.ConfigWrapper.load_from_file")
def test_a_file_of_comments_only_gives_the_defaults(
        write_config: Callable[[str], str]) -> None:
    """Stripping every line leaves an empty configuration, not an error."""

    Config.load_from_file(write_config("# nothing\n# but notes\n"))

    assert Config.lives >= 1


@verifies("src.config.ConfigWrapper.load_from_file")
def test_a_json_list_is_reported(
        write_config: Callable[[str], str]) -> None:
    """The config file must hold an object, not an array."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('[1, 2, 3]'))


@verifies("src.config.ConfigWrapper.load_from_file")
def test_a_json_scalar_is_reported(
        write_config: Callable[[str], str]) -> None:
    """A bare number is not a configuration either."""

    with pytest.raises(ConfigError):
        Config.load_from_file(write_config('42'))


@verifies("src.config.ConfigWrapper.load_from_file")
def test_non_utf8_bytes_are_reported(tmp_path: Path) -> None:
    """A binary file raises ConfigError, not UnicodeDecodeError."""

    path = tmp_path / "binary.json"
    path.write_bytes(b'{"lives": 3}\xff\xfe')

    with pytest.raises(ConfigError):
        Config.load_from_file(str(path))


@verifies("src.config.ConfigWrapper.load_from_file")
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


@verifies("src.config.ConfigWrapper.load_from_file")
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


@verifies("src.config.ConfigWrapper.load_from_file")
def test_the_name_length_limit_is_configurable(
        write_config: Callable[[str], str]) -> None:
    """The leaderboard name limit comes from the config."""

    Config.load_from_file(write_config('{"name_length": 4}'))

    assert Config.name_length == 4


@verifies("src.config.ConfigWrapper.ms_per_tick")
def test_the_frame_and_tick_rates_are_configured() -> None:
    """The game draws several frames for each logic tick."""

    assert Config.framerate >= 1
    assert Config.ticks_per_sec >= 1
    assert Config.ms_per_tick > 1000 // Config.framerate


@verifies("src.config.ConfigWrapper.ms_per_tick")
def test_the_default_config_ticks_four_times_a_second() -> None:
    """Four steps a second is the rate the gameplay was tuned for."""

    assert Config.ticks_per_sec == 4
    assert Config.ms_per_tick == 250
