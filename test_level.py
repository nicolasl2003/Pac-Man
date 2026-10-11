"""A level runs, ends, and keeps the run going across stages."""

from typing import Callable

from src import Config, Direction, GameState, Level

from gaps import missing


def test_a_fresh_level_is_running(
        open_level: Callable[..., Level]) -> None:
    """Nothing is won or lost before the first tick."""

    level = open_level()

    assert level.state is Level.State.RUNNING


def test_a_fresh_level_is_fully_furnished(
        open_level: Callable[..., Level]) -> None:
    """A level owns its maze, its player, its ghosts and its pacgums."""

    level = open_level()

    assert level.maze is GameState.level.maze
    assert level.player.cell in level.maze.cell_dict.values()
    assert len(level.ghosts) == Config.ghost_count
    assert level.pacgums


def test_a_new_level_starts_the_run_timer(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """The configured time limit is loaded when the level opens."""

    Config.load_from_file(write_config('{"level_time": 42}'))

    open_level()

    assert GameState.timer == 42


def test_a_level_can_be_lost(
        open_level: Callable[..., Level]) -> None:
    """Losing is a state the caller can read."""

    level = open_level()

    level.lost()

    assert level.state is Level.State.LOST


@missing("Maze.center, the middle spawn cell of the player")
def test_the_player_starts_in_the_middle(
        open_level: Callable[..., Level]) -> None:
    """The spawn is the centre cell of the maze, away from the ghosts."""

    level = open_level()

    assert level.player.cell.pos == (7, 7)


@missing("Player.tick, so a level cannot be ticked yet")
def test_a_tick_advances_the_timer(
        open_level: Callable[..., Level]) -> None:
    """Time passes while the level runs."""

    level = open_level()
    level.ghosts.clear()
    before = GameState.timer

    level.tick()

    assert GameState.timer < before


@missing("Player.tick, so a level cannot be ticked yet")
def test_a_tick_reports_the_state(
        open_level: Callable[..., Level]) -> None:
    """The tick returns what the caller needs to branch on."""

    level = open_level()
    level.ghosts.clear()

    assert level.tick() is level.state


@missing("Player.tick, which applies the current direction")
def test_the_player_walks_in_its_current_direction(
        open_level: Callable[..., Level]) -> None:
    """A direction set once keeps applying on every tick."""

    level = open_level()
    level.ghosts.clear()
    level.player.cell = level.maze.get_cell(5, 5)
    level.player.direction = Direction.RIGHT

    level.tick()
    level.tick()

    assert level.player.cell.pos == (7, 5)


@missing("Player.tick, which applies the current direction")
def test_a_wall_stops_the_player_without_ending_the_level(
        open_level: Callable[..., Level]) -> None:
    """Pushing into the border is harmless."""

    level = open_level()
    level.ghosts.clear()
    level.player.cell = level.maze.get_cell(0, 5)
    level.player.direction = Direction.LEFT

    level.tick()

    assert level.player.cell.pos == (0, 5)
    assert level.state is Level.State.RUNNING


@missing("Player.tick, so the timer cannot run down yet")
def test_running_out_of_time_loses_the_level(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """The configured time limit ends the level."""

    Config.load_from_file(write_config('{"level_time": 3}'))
    level = open_level()
    level.ghosts.clear()

    for _ in range(Config.level_time + 1):
        level.tick()

    assert level.state is Level.State.LOST


@missing("losing a life when a ghost catches the player")
def test_losing_the_last_life_loses_the_level(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """The level ends when no life is left."""

    Config.load_from_file(write_config('{"lives": 1}'))
    GameState.reset()
    level = open_level()
    ghost = level.ghosts[0]
    del level.ghosts[1:]
    level.player.cell = level.maze.get_cell(7, 7)
    ghost.cell = level.maze.get_cell(7, 6)

    level.tick()

    assert GameState.lives == 0
    assert level.state is Level.State.LOST


@missing("losing a life when a ghost catches the player")
def test_a_lost_life_does_not_end_the_level_on_its_own(
        open_level: Callable[..., Level]) -> None:
    """With lives left, being caught only resets the positions."""

    level = open_level()
    ghost = level.ghosts[0]
    del level.ghosts[1:]
    level.player.cell = level.maze.get_cell(7, 7)
    ghost.cell = level.maze.get_cell(7, 6)

    level.tick()

    assert GameState.lives >= 1
    assert level.state is Level.State.RUNNING
    assert ghost.cell is ghost.spawn


@missing("a finished level refusing to tick any further")
def test_a_finished_level_stops_moving(
        open_level: Callable[..., Level]) -> None:
    """Ticking a lost level changes nothing."""

    level = open_level()
    level.ghosts.clear()
    level.lost()
    before = GameState.timer

    level.tick()

    assert GameState.timer == before


@missing("Level.update, the drawing pass of the level")
def test_a_level_can_be_drawn(
        open_level: Callable[..., Level]) -> None:
    """One frame of the level is drawn without raising."""

    open_level().update(16)
