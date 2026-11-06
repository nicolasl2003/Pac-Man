"""A level that runs out of time is retried or given up on, not lost."""

from typing import Callable, Iterator

import pytest

from src import Config, GameState, Level

from capabilities import times_out_without_losing
from gaps import missing
from helpers import remove_ghosts
from review import verifies

_MISSING = missing("a timeout the run survives",
                   when=not times_out_without_losing(),
                   raises=(AttributeError, AssertionError))


@pytest.fixture(autouse=True)
def short_level(write_config: Callable[[str], str]) -> Iterator[None]:
    """Opens a run whose level times out after a few ticks."""

    Config.load_from_file(write_config('{"level_time": 3}'))
    GameState.reset()
    remove_ghosts(GameState.level)
    yield


def _run_out_of_time() -> None:
    """Ticks the current level until its timer is empty."""

    for _ in range(Config.level_time * 1000 // Config.ms_per_tick + 1):
        GameState.level.tick()


@_MISSING
@verifies("src.level.Level.tick")
def test_running_out_of_time_times_the_level_out() -> None:
    """The level stops on its own state, not on a loss."""

    _run_out_of_time()

    assert GameState.level.state is Level.State.TIMEDOUT


@verifies("src.level.Level.tick")
def test_running_out_of_time_costs_no_life() -> None:
    """The player still holds every life of the run."""

    lives: int = GameState.lives
    _run_out_of_time()

    assert GameState.lives == lives


@_MISSING
@verifies("src.game_state.GameStateModel.retry_stage")
def test_a_retry_opens_the_level_again() -> None:
    """A retried level is running, on a full timer."""

    _run_out_of_time()
    GameState.retry_stage()

    assert GameState.level.state is Level.State.RUNNING
    assert GameState.timer == Config.level_time * 1000 // Config.ms_per_tick


@_MISSING
@verifies("src.game_state.GameStateModel.retry_stage")
def test_a_retry_gives_back_the_score_of_the_start_of_the_level() -> None:
    """The points of the failed attempt are not kept."""

    GameState.score = 777
    _run_out_of_time()
    GameState.retry_stage()

    assert GameState.score == GameState.starting_score


@_MISSING
@verifies("src.game_state.GameStateModel.retry_stage")
def test_a_retry_keeps_the_score_of_the_levels_already_won() -> None:
    """A retry on the second level keeps what the first one earned."""

    GameState.score = 120
    assert GameState.next_stage()
    GameState.score += 50
    _run_out_of_time()
    GameState.retry_stage()

    assert GameState.score == 120


@_MISSING
@verifies("src.game_state.GameStateModel.retry_stage")
def test_a_retry_plays_the_same_maze() -> None:
    """The maze of a retry is the one the level was played on."""

    walls: list[int] = [cell.walls for cell
                        in GameState.level.maze.cell_dict.values()]
    _run_out_of_time()
    GameState.retry_stage()

    assert [cell.walls for cell
            in GameState.level.maze.cell_dict.values()] == walls


@_MISSING
@verifies("src.game_state.GameStateModel.retry_stage")
def test_a_retry_costs_no_life() -> None:
    """Giving the level another go is free."""

    lives: int = GameState.lives
    _run_out_of_time()
    GameState.retry_stage()

    assert GameState.lives == lives


@_MISSING
@verifies("src.game_state.GameStateModel.give_up")
def test_giving_up_loses_the_run() -> None:
    """A player who gives up goes to the end screen as a loser."""

    _run_out_of_time()
    GameState.give_up()

    assert GameState.level.state is Level.State.LOST
