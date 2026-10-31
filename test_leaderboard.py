"""The leaderboard is the persistent highscore table of the game.

The code keeps it in src.scores, as a json list of name and score rows.
"""

import json
import os
from pathlib import Path
from typing import Callable

import pytest
from pydantic import BaseModel

from src import Config
from src.scores import load_scores, save_score

from capabilities import drops_only_a_mistyped_score
from gaps import known_bug
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


@verifies("src.scores.save_score")
def test_adding_a_score_keeps_it() -> None:
    """A finished game lands in the table."""

    save_score("Sannaka", 1110)

    assert load_scores() == [{"name": "Sannaka", "score": 1110}]


@verifies("src.scores.load_scores")
def test_the_configured_file_is_the_one_used() -> None:
    """Saving with no path writes where the config points."""

    save_score("Sannaka", 1110)

    assert Path(Config.highscore_filename).exists()
    assert load_scores(Config.highscore_filename) == load_scores()


@verifies("src.scores.save_score")
def test_scores_are_sorted_from_best_to_worst() -> None:
    """The table reads like an arcade cabinet."""

    for name, score in (("low", 10), ("high", 900), ("mid", 300)):
        save_score(name, score)

    assert [row["score"] for row in load_scores()] == [900, 300, 10]


@verifies("src.scores.save_score")
def test_the_same_player_can_appear_twice() -> None:
    """Beating your own score does not replace the older row."""

    save_score("goldfish", 20)
    save_score("goldfish", 50)

    assert [row["name"] for row in load_scores()] == ["goldfish", "goldfish"]


@verifies("src.scores.save_score")
def test_an_identical_row_can_appear_twice() -> None:
    """Two runs with the same name and score both stay."""

    save_score("foliole", 20)
    save_score("foliole", 20)

    assert len(load_scores()) == 2


@verifies("src.scores.save_score")
def test_an_empty_name_is_replaced() -> None:
    """A player who types nothing still gets a row."""

    save_score("", 20)

    assert load_scores()[0]["name"] != ""


@verifies("src.scores.save_score")
def test_a_space_in_a_name_is_kept() -> None:
    """The subject allows spaces in a name."""

    save_score("two words", 20)

    assert load_scores()[0]["name"] == "two words"


@verifies("src.scores.save_score")
def test_the_saved_file_is_a_list_of_name_and_score_dicts(
        tmp_path: Path) -> None:
    """The file on disk is the documented list of dicts."""

    path = tmp_path / "scores.json"
    save_score("Sannaka", 1110, str(path))

    assert json.loads(path.read_text()) == [{"name": "Sannaka",
                                             "score": 1110}]


@verifies("src.scores.save_score")
def test_the_table_is_parsable_by_pydantic() -> None:
    """An outside reader can validate the rows without the game."""

    save_score("Sannaka", 1110)
    save_score("foliole", 20)
    rows = [_Entry(**row) for row in load_scores()]

    assert [row.name for row in rows] == ["Sannaka", "foliole"]


@verifies("src.scores.load_scores")
def test_the_table_survives_a_json_round_trip() -> None:
    """The table holds json types only."""

    save_score("Sannaka", 1110)

    assert json.loads(json.dumps(load_scores())) == load_scores()


@verifies("src.scores.save_score")
def test_saving_then_loading_gives_the_same_table(tmp_path: Path) -> None:
    """A table written to disk comes back unchanged."""

    path = str(tmp_path / "scores.json")
    save_score("Sannaka", 1110, path)
    save_score("foliole", 20, path)

    assert load_scores(path) == [{"name": "Sannaka", "score": 1110},
                                 {"name": "foliole", "score": 20}]


@verifies("src.scores.load_scores")
def test_a_missing_file_leaves_an_empty_table() -> None:
    """A first run has no file yet, and must not crash."""

    assert load_scores("/nonexistent/pacman/highscores.json") == []


@verifies("src.scores.load_scores")
def test_a_broken_file_leaves_an_empty_table(
        write_scores: Callable[[str], str]) -> None:
    """Invalid json is dropped instead of raising."""

    assert load_scores(write_scores('{"oops": ')) == []


@verifies("src.scores.load_scores")
def test_a_file_holding_an_object_leaves_an_empty_table(
        write_scores: Callable[[str], str]) -> None:
    """The file must hold a list of rows."""

    assert load_scores(write_scores('{"name": "x", "score": 1}')) == []


@verifies("src.scores.load_scores")
def test_unusable_rows_are_skipped(
        write_scores: Callable[[str], str]) -> None:
    """One bad row does not throw the whole table away."""

    path = write_scores(json.dumps([
        {"name": "Sannaka", "score": 1110},
        {"name": "missing score"},
        {"score": 50},
        "not a row",
        {"name": "goldfish", "score": 20},
    ]))

    assert [row["name"] for row in load_scores(path)] == ["Sannaka",
                                                          "goldfish"]


@known_bug("a mistyped score drops the whole table",
           when=not drops_only_a_mistyped_score(),
           raises=AssertionError)
@verifies("src.scores.load_scores")
def test_a_mistyped_score_only_drops_its_own_row(
        write_scores: Callable[[str], str]) -> None:
    """The rows around a score that is not a number are kept."""

    path = write_scores(json.dumps([
        {"name": "Sannaka", "score": 1110},
        {"name": "foliole", "score": "twenty"},
    ]))

    assert [row["name"] for row in load_scores(path)] == ["Sannaka"]


@verifies("src.scores.save_score")
def test_saving_does_not_leak_file_handles(tmp_path: Path) -> None:
    """Writing the table many times closes every file."""

    if not Path("/proc/self/fd").exists():
        pytest.skip("no /proc on this platform")
    path = str(tmp_path / "scores.json")
    save_score("Sannaka", 1110, path)
    opened = len(os.listdir("/proc/self/fd"))

    for _ in range(50):
        save_score("Sannaka", 1110, path)
        load_scores(path)

    assert len(os.listdir("/proc/self/fd")) <= opened + 1


@verifies("src.scores.save_score")
def test_only_the_top_ten_are_kept() -> None:
    """The eleventh best score falls off the table."""

    for score in range(1, 13):
        save_score(f"p{score}", score * 10)

    assert len(load_scores()) == 10
    assert min(row["score"] for row in load_scores()) == 30


@verifies("src.scores.load_scores")
def test_a_loaded_file_is_still_capped_at_ten(
        write_scores: Callable[[str], str]) -> None:
    """A file with twenty rows loads the ten best."""

    path = write_scores(json.dumps(
        [{"name": f"p{i}", "score": i} for i in range(20)]))

    assert len(load_scores(path)) == 10


@verifies("src.scores.save_score")
def test_a_long_name_is_cut_to_the_configured_length(
        write_config: Callable[[str], str]) -> None:
    """Config.name_length caps what a player can type."""

    Config.load_from_file(write_config('{"name_length": 4}'))
    save_score("Marmelade", 20)

    assert load_scores()[0]["name"] == "Marm"


@verifies("src.scores.save_score")
def test_a_name_keeps_only_letters_digits_and_spaces() -> None:
    """The subject allows alphanumeric characters and spaces."""

    save_score("a_b!c 1", 20)

    assert load_scores()[0]["name"] == "abc 1"


@verifies("src.scores.save_score")
def test_a_negative_score_is_refused() -> None:
    """Scores are non-negative integers."""

    save_score("cheater", -5)

    assert all(row["score"] >= 0 for row in load_scores())
