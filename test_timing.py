"""Ticks drive the logic, frames only interpolate between two ticks.

None of the interpolation exists yet: the entities draw themselves on
their cell, and update raises. Every test here waits on that pass.
"""

from typing import Callable

import pytest

from src import Config, Direction, GameState, Level, Maze

from gaps import missing
from helpers import open_edges, open_grid


def _tick_ms() -> float:
    """Returns how long one logic tick lasts, in milliseconds."""

    return 1000 * Config.frame_per_tick / Config.framerate


def test_one_tick_lasts_several_frames() -> None:
    """The frame budget of a tick is what the drawing interpolates over."""

    assert _tick_ms() > 1000 / Config.framerate


@missing("the visual transition between two cells")
def test_a_still_entity_sits_on_its_cell(
        open_level: Callable[..., Level]) -> None:
    """With no move pending there is nothing to interpolate."""

    player = open_level().player

    assert player.progress == 1  # type: ignore[attr-defined]
    assert (player.x, player.y) == player.cell.pos


@missing("the visual transition between two cells")
def test_moving_restarts_the_transition(
        open_level: Callable[..., Level]) -> None:
    """Right after a move the drawing is still on the old cell."""

    level = open_level()
    player = level.player
    start = player.cell
    player.move(Direction.RIGHT)

    assert player.previous_cell is start  # type: ignore[attr-defined]
    assert player.progress == 0  # type: ignore[attr-defined]
    assert (player.x, player.y) == start.pos


@missing("the visual transition between two cells")
def test_half_a_tick_draws_the_entity_halfway(
        open_level: Callable[..., Level]) -> None:
    """A frame in the middle of a tick sits between the two cells."""

    level = open_level()
    player = level.player
    start_x = player.cell.x
    player.move(Direction.RIGHT)
    player.update(round(_tick_ms() / 2))

    assert player.x == start_x + 0.5
    assert player.y == player.cell.y


@missing("the visual transition between two cells")
def test_a_full_tick_lands_on_the_new_cell(
        open_level: Callable[..., Level]) -> None:
    """At the end of the tick the drawing has caught up."""

    level = open_level()
    player = level.player
    player.move(Direction.DOWN)
    player.update(round(_tick_ms()))

    assert player.progress == 1  # type: ignore[attr-defined]
    assert (player.x, player.y) == player.cell.pos


@missing("the visual transition between two cells")
def test_several_frames_add_up_to_one_tick(
        open_level: Callable[..., Level]) -> None:
    """Frames accumulate, they do not restart the transition."""

    level = open_level()
    player = level.player
    player.move(Direction.RIGHT)
    for _ in range(5):
        player.update(round(_tick_ms() / 5))

    assert player.progress == pytest.approx(1)  # type: ignore[attr-defined]
    assert (player.x, player.y) == pytest.approx(player.cell.pos)


@missing("the visual transition between two cells")
def test_the_transition_never_overshoots(
        open_level: Callable[..., Level]) -> None:
    """A long frame clamps the transition instead of flying past."""

    level = open_level()
    player = level.player
    player.move(Direction.RIGHT)
    player.update(round(_tick_ms()) * 10)

    assert player.progress == 1  # type: ignore[attr-defined]
    assert (player.x, player.y) == player.cell.pos


@missing("the visual transition between two cells")
def test_a_blocked_move_leaves_the_drawing_alone(
        open_level: Callable[..., Level]) -> None:
    """A refused move must not start a transition from nowhere."""

    level = open_level()
    player = level.player
    player.cell = level.maze.get_cell(0, 5)
    player.move(Direction.LEFT)
    player.update(round(_tick_ms() / 2))

    assert (player.x, player.y) == (0, 5)


@missing("the visual transition between two cells")
def test_a_ghost_is_interpolated_too(
        open_level: Callable[..., Level]) -> None:
    """Ghosts use the same transition as the player."""

    level = open_level()
    ghost = level.ghosts[0]
    ghost.cell = level.maze.get_cell(5, 5)
    ghost.move(Direction.RIGHT)
    ghost.update(round(_tick_ms() / 2))

    assert ghost.x == 5.5


@missing("tunnels, and the short way to draw a move across one")
def test_a_wrapping_move_is_drawn_the_short_way() -> None:
    """Crossing the edge must not slide across the whole maze."""

    maze = Maze(open_edges(open_grid(15, 15)))
    level = Level(maze)
    GameState.level = level
    player = level.player
    player.cell = maze.get_cell(0, 7)
    player.move(Direction.LEFT)
    player.update(round(_tick_ms() / 2))

    assert player.cell.pos == (14, 7)
    assert abs(player.x - 14) <= 1 or abs(player.x - (-1)) <= 1
