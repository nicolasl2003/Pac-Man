"""A level runs, ends, and keeps the run going across stages."""

from typing import Callable

from src import Config, Direction, GameState, Level

from helpers import remove_ghosts
from review import verifies


@verifies("src.level.Level.__init__")
def test_a_fresh_level_is_running(
        open_level: Callable[..., Level]) -> None:
    """Nothing is won or lost before the first tick."""

    level = open_level()

    assert level.state is Level.State.RUNNING


@verifies("src.level.Level.__init__")
def test_a_fresh_level_is_fully_furnished(
        open_level: Callable[..., Level]) -> None:
    """A level owns its maze, its player, its ghosts and its pacgums."""

    level = open_level()

    assert level.maze is GameState.level.maze
    assert level.player.cell in level.maze.cell_dict.values()
    assert len(level.ghosts) == Config.ghost_count
    assert level.pacgums


@verifies("src.game_state.GameStateModel.reset_timer")
def test_a_new_level_starts_the_run_timer(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """The configured time limit is loaded when the level opens."""

    Config.load_from_file(write_config('{"level_time": 42}'))

    open_level()

    assert GameState.timer == 42 * 1000 // Config.ms_per_tick


@verifies("src.level.Level.lost")
def test_a_level_can_be_lost(
        open_level: Callable[..., Level]) -> None:
    """Losing is a state the caller can read."""

    level = open_level()

    level.lost()

    assert level.state is Level.State.LOST


@verifies("src.level.Level.__init__")
def test_the_player_starts_in_the_middle(
        open_level: Callable[..., Level]) -> None:
    """The spawn is the centre cell of the maze, away from the ghosts."""

    level = open_level()

    assert level.player.cell.pos == (7, 7)


@verifies("src.level.Level.tick")
def test_a_tick_advances_the_timer(
        open_level: Callable[..., Level]) -> None:
    """Time passes while the level runs."""

    level = open_level()
    remove_ghosts(level)
    before = GameState.timer

    level.tick()

    assert GameState.timer < before


@verifies("src.level.Level.tick")
def test_a_tick_reports_the_state(
        open_level: Callable[..., Level]) -> None:
    """The tick returns what the caller needs to branch on."""

    level = open_level()
    remove_ghosts(level)

    assert level.tick() is level.state


@verifies("src.level.Level.tick")
def test_the_player_walks_in_its_current_direction(
        open_level: Callable[..., Level]) -> None:
    """A direction set once keeps applying on every tick."""

    level = open_level()
    remove_ghosts(level)
    level.player.cell = level.maze.get_cell(5, 5)
    level.player.set_direction(Direction.RIGHT)

    level.tick()
    level.tick()

    assert level.player.cell.pos == (7, 5)


@verifies("src.level.Level.tick")
def test_a_wall_stops_the_player_without_ending_the_level(
        open_level: Callable[..., Level]) -> None:
    """Pushing into the border is harmless."""

    level = open_level()
    remove_ghosts(level)
    level.player.cell = level.maze.get_cell(0, 5)
    level.player.set_direction(Direction.LEFT)

    level.tick()

    assert level.player.cell.pos == (0, 5)
    assert level.state is Level.State.RUNNING


@verifies("src.level.Level.tick")
def test_running_out_of_time_ends_the_level(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """The configured time limit ends the level, won or not.

    A branch telling a timeout apart from a loss is covered on its own.
    """

    Config.load_from_file(write_config('{"level_time": 3}'))
    level = open_level()
    remove_ghosts(level)

    ticks = Config.level_time * 1000 // Config.ms_per_tick
    for _ in range(ticks + 1):
        level.tick()

    assert level.state not in (Level.State.RUNNING, Level.State.WON)


@verifies("src.level.Level.tick")
def test_losing_the_last_life_loses_the_level(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """A ghost met on a move that takes the last life ends the level."""

    Config.load_from_file(write_config('{"lives": 1}'))
    GameState.reset()
    level = open_level()
    ghost = level.ghosts[0]
    del level.ghosts[1:]
    level.player.cell = level.maze.get_cell(7, 7)
    ghost.cell = level.maze.get_cell(7, 6)

    level.player.move(Direction.UP)

    assert GameState.lives == 0
    assert level.state is Level.State.LOST


@verifies("src.level.Level.tick")
def test_a_lost_life_does_not_end_the_level_on_its_own(
        open_level: Callable[..., Level]) -> None:
    """With lives left, meeting a ghost only resets the positions."""

    level = open_level()
    ghost = level.ghosts[0]
    del level.ghosts[1:]
    level.player.cell = level.maze.get_cell(7, 7)
    ghost.cell = level.maze.get_cell(7, 6)

    level.player.move(Direction.UP)

    assert GameState.lives >= 1
    assert level.state is Level.State.RUNNING
    assert ghost.cell is ghost.spawn


@verifies("src.level.Level.lose_life")
def test_lose_life_takes_a_life_and_sends_everyone_home(
        open_level: Callable[..., Level]) -> None:
    """With lives left, the player and the ghosts go back to their spawn."""

    level = open_level()
    lives = GameState.lives
    level.player.cell = level.maze.get_cell(1, 1)
    level.ghosts[0].cell = level.maze.get_cell(7, 6)

    level.lose_life()

    assert GameState.lives == lives - 1
    assert level.player.cell is level.player.spawn
    assert level.ghosts[0].cell is level.ghosts[0].spawn
    assert level.state is Level.State.RUNNING


@verifies("src.level.Level.lose_life")
def test_lose_life_on_the_last_life_loses_the_level(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """No life left ends the level."""

    Config.load_from_file(write_config('{"lives": 1}'))
    GameState.reset()
    level = open_level()

    level.lose_life()

    assert GameState.lives == 0
    assert level.state is Level.State.LOST


@verifies("src.level.Level.tick")
def test_a_finished_level_stops_moving(
        open_level: Callable[..., Level]) -> None:
    """Ticking a lost level changes nothing."""

    level = open_level()
    remove_ghosts(level)
    level.lost()
    before = GameState.timer

    level.tick()

    assert GameState.timer == before
