"""The leaderboard is the persistent highscore table of the game.

The code keeps it in src.scores, as pydantic rows saved as a json list.
"""

import json
import os
from pathlib import Path
from typing import Callable

import pytest
from pydantic import BaseModel

from src import Config
from src.scores import load_scores, save_score

from capabilities import drops_only_a_mistyped_score, keeps_scores_as_models
from gaps import known_bug, missing
from review import verifies


class _Entry(BaseModel):
    """A row as an outside reader would parse it.

    name -- the player name
    score -- the points of the run
    """

    name: str
    score: int


@verifies("src.scores.load_scores")
def test_a_fresh_leaderboard_is_empty() -> None:
    """Nothing is scored before a game is played."""

    assert load_scores() == []


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_adding_a_score_keeps_it() -> None:
    """A finished game lands in the table."""

    save_score("Sannaka", 1110)

    assert [row.model_dump() for row in load_scores()] == [
        {"name": "Sannaka", "score": 1110}]


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(),
         raises=(AttributeError, AssertionError))
@verifies("src.scores.Score")
def test_a_row_is_a_pydantic_model() -> None:
    """The table hands back validated rows, not bare dicts."""

    save_score("Sannaka", 1110)

    assert all(isinstance(row, BaseModel) for row in load_scores())


@verifies("src.scores.load_scores")
def test_the_configured_file_is_the_one_used() -> None:
    """Saving writes where the config points, and loading reads it back."""

    save_score("Sannaka", 1110)

    assert Path(Config.highscore_filename).exists()
    assert len(load_scores()) == 1


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_scores_are_sorted_from_best_to_worst() -> None:
    """The table reads like an arcade cabinet."""

    for name, score in (("low", 10), ("high", 900), ("mid", 300)):
        save_score(name, score)

    assert [row.score for row in load_scores()] == [900, 300, 10]


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_the_same_player_can_appear_twice() -> None:
    """Beating your own score does not replace the older row."""

    save_score("goldfish", 20)
    save_score("goldfish", 50)

    assert [row.name for row in load_scores()] == ["goldfish", "goldfish"]


@verifies("src.scores.save_score")
def test_an_identical_row_can_appear_twice() -> None:
    """Two runs with the same name and score both stay."""

    save_score("foliole", 20)
    save_score("foliole", 20)

    assert len(load_scores()) == 2


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_an_empty_name_is_replaced() -> None:
    """A player who types nothing still gets a row."""

    save_score("", 20)

    assert load_scores()[0].name != ""


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_a_space_in_a_name_is_kept() -> None:
    """The subject allows spaces in a name."""

    save_score("two words", 20)

    assert load_scores()[0].name == "two words"


@verifies("src.scores.save_score")
def test_the_saved_file_is_a_list_of_name_and_score_dicts() -> None:
    """The file on disk is the documented list of dicts."""

    save_score("Sannaka", 1110)

    assert json.loads(Path(Config.highscore_filename).read_text()) == [
        {"name": "Sannaka", "score": 1110}]


@verifies("src.scores.save_score")
def test_the_saved_file_is_parsable_by_pydantic() -> None:
    """An outside reader can validate the file without the game."""

    save_score("Sannaka", 1110)
    save_score("foliole", 20)
    saved = json.loads(Path(Config.highscore_filename).read_text())

    assert [_Entry.model_validate(row).name for row in saved] == [
        "Sannaka", "foliole"]


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.load_scores")
def test_the_table_survives_a_json_round_trip() -> None:
    """A row holds json types only."""

    save_score("Sannaka", 1110)
    rows = [row.model_dump() for row in load_scores()]

    assert json.loads(json.dumps(rows)) == rows


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_saving_then_loading_gives_the_same_table() -> None:
    """A table written to disk comes back unchanged."""

    save_score("Sannaka", 1110)
    save_score("foliole", 20)

    assert [row.model_dump() for row in load_scores()] == [
        {"name": "Sannaka", "score": 1110}, {"name": "foliole", "score": 20}]


@verifies("src.scores.load_scores")
def test_a_missing_file_leaves_an_empty_table(
        write_config: Callable[[str], str]) -> None:
    """A first run has no file yet, and must not crash."""

    Config.load_from_file(write_config(
        '{"highscore_filename": "/nonexistent/pacman/highscores.json"}'))

    assert load_scores() == []


@verifies("src.scores.load_scores")
def test_a_broken_file_leaves_an_empty_table(
        write_scores: Callable[[str], str]) -> None:
    """Invalid json is dropped instead of raising."""

    write_scores('{"oops": ')

    assert load_scores() == []


@verifies("src.scores.load_scores")
def test_a_file_holding_an_object_leaves_an_empty_table(
        write_scores: Callable[[str], str]) -> None:
    """The file must hold a list of rows."""

    write_scores('{"name": "x", "score": 1}')

    assert load_scores() == []


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.load_scores")
def test_unusable_rows_are_skipped(
        write_scores: Callable[[str], str]) -> None:
    """One bad row does not throw the whole table away."""

    write_scores(json.dumps([
        {"name": "Sannaka", "score": 1110},
        {"name": "missing score"},
        {"score": 50},
        "not a row",
        {"name": "goldfish", "score": 20},
    ]))

    assert [row.name for row in load_scores()] == ["Sannaka", "goldfish"]


@known_bug("a mistyped score drops the whole table",
           when=not drops_only_a_mistyped_score(),
           raises=(AssertionError, AttributeError))
@verifies("src.scores.load_scores")
def test_a_mistyped_score_only_drops_its_own_row(
        write_scores: Callable[[str], str]) -> None:
    """The rows around a score that is not a number are kept."""

    write_scores(json.dumps([
        {"name": "Sannaka", "score": 1110},
        {"name": "foliole", "score": "twenty"},
    ]))

    assert [row.name for row in load_scores()] == ["Sannaka"]


@verifies("src.scores.save_score")
def test_saving_does_not_leak_file_handles() -> None:
    """Writing the table many times closes every file."""

    if not Path("/proc/self/fd").exists():
        pytest.skip("no /proc on this platform")
    save_score("Sannaka", 1110)
    opened = len(os.listdir("/proc/self/fd"))

    for _ in range(50):
        save_score("Sannaka", 1110)
        load_scores()

    assert len(os.listdir("/proc/self/fd")) <= opened + 1


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_only_the_top_ten_are_kept() -> None:
    """The eleventh best score falls off the table."""

    for score in range(1, 13):
        save_score(f"p{score}", score * 10)

    assert len(load_scores()) == 10
    assert min(row.score for row in load_scores()) == 30


@verifies("src.scores.load_scores")
def test_a_loaded_file_is_still_capped_at_ten(
        write_scores: Callable[[str], str]) -> None:
    """A file with twenty rows loads the ten best."""

    write_scores(json.dumps(
        [{"name": f"p{i}", "score": i} for i in range(20)]))

    assert len(load_scores()) == 10


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_a_long_name_is_cut_to_the_configured_length(
        write_config: Callable[[str], str]) -> None:
    """Config.name_length caps what a player can type."""

    Config.load_from_file(write_config('{"name_length": 4}'))
    save_score("Marmelade", 20)

    assert load_scores()[0].name == "Marm"


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_a_name_keeps_only_letters_digits_and_spaces() -> None:
    """The subject allows alphanumeric characters and spaces."""

    save_score("a_b!c 1", 20)

    assert load_scores()[0].name == "abc 1"


@verifies("src.scores.save_score")
def test_a_negative_score_is_refused() -> None:
    """Scores are non-negative integers."""

    save_score("cheater", -5)

    assert all(row.score >= 0 for row in load_scores())
