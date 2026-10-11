"""Score and lives follow the player from one stage to the next."""

from random import Random
from typing import Callable

from src import Config, GameState, Level

from src.scores import load_scores, save_score

from gaps import missing


def _clear_the_level(level: Level) -> None:
    """Eats every pacgum of a level, ghosts removed.

    level -- the level to empty
    """

    level.ghosts.clear()
    for gum in list(level.pacgums):
        level.player.cell = gum.cell
        level.tick()


def test_a_new_run_starts_at_the_first_stage() -> None:
    """A game opens on stage zero with a full score sheet."""

    assert GameState.stage == 0
    assert GameState.score == 0
    assert GameState.lives == Config.lives


def test_a_new_run_clears_the_score_and_the_stage() -> None:
    """Losing everything starts the next game from scratch."""

    GameState.score = 500
    GameState.stage = 4
    GameState.lives = 0
    GameState.reset()

    assert (GameState.score, GameState.stage) == (0, 0)
    assert GameState.lives == Config.lives


def test_a_new_run_opens_a_running_level() -> None:
    """A reset hands back a level ready to play."""

    GameState.reset()

    assert GameState.level.state is Level.State.RUNNING
    assert GameState.level.pacgums


def test_a_new_run_seeds_its_own_random_source(
        write_config: Callable[[str], str]) -> None:
    """The run carries the generator every random choice must use."""

    Config.load_from_file(write_config('{"seed": 42}'))
    GameState.reset()

    assert isinstance(GameState.random, Random)
    assert GameState.random.random() == Random(42).random()


def test_a_finished_run_can_be_saved_to_the_leaderboard() -> None:
    """The score of a finished run is what the table receives."""

    GameState.score = 1234
    save_score("Sannaka", GameState.score)

    assert load_scores()[0] == {"name": "Sannaka", "score": 1234}


@missing("GameState.next_stage, the move to the following level")
def test_winning_a_stage_keeps_the_score(
        write_config: Callable[[str], str]) -> None:
    """Points earned stay earned across stages."""

    Config.load_from_file(write_config('{"level_time": 500}'))
    GameState.reset()
    _clear_the_level(GameState.level)
    earned = GameState.score
    GameState.next_stage()  # type: ignore[attr-defined]

    assert GameState.score == earned
    assert earned > 0


@missing("GameState.next_stage, the move to the following level")
def test_winning_a_stage_keeps_the_lives(
        write_config: Callable[[str], str]) -> None:
    """A life lost on stage one is still lost on stage two."""

    Config.load_from_file(write_config('{"level_time": 500}'))
    GameState.reset()
    GameState.lives -= 1
    remaining = GameState.lives
    _clear_the_level(GameState.level)
    GameState.next_stage()  # type: ignore[attr-defined]

    assert GameState.lives == remaining


@missing("GameState.next_stage, the move to the following level")
def test_the_next_stage_counts_up(
        write_config: Callable[[str], str]) -> None:
    """The stage number is what the HUD shows."""

    Config.load_from_file(write_config('{"level_time": 500}'))
    GameState.reset()
    _clear_the_level(GameState.level)
    GameState.next_stage()  # type: ignore[attr-defined]

    assert GameState.stage == 1


@missing("GameState.stage_count, the ten levels the subject asks for")
def test_the_game_has_at_least_ten_stages() -> None:
    """The subject asks for ten levels or more."""

    assert GameState.stage_count >= 10  # type: ignore[attr-defined]


@missing("GameState.reset keeping the session highscore")
def test_a_new_run_keeps_the_session_highscore() -> None:
    """The best score of the session outlives a run."""

    GameState.highscore = 999
    GameState.reset()

    assert GameState.highscore == 999


@missing("the highscore following the score as it grows")
def test_the_highscore_follows_the_best_score(
        write_config: Callable[[str], str]) -> None:
    """Scoring past the session best raises it."""

    Config.load_from_file(write_config('{"level_time": 500}'))
    GameState.reset()
    _clear_the_level(GameState.level)

    assert GameState.highscore == GameState.score
