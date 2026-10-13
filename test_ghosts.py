"""Ghosts chase the player, flee when frightened, and can be eaten."""

from typing import Callable

import pytest

from src import Config, GameState, Ghost, Level, Maze
from src.entities import NotEdibleError

from gaps import known_bug
from helpers import distance, open_grid


def _lone_ghost(level: Level) -> Ghost:
    """Keeps a single ghost in the level and returns it.

    level -- the level to strip down to one ghost
    """

    del level.ghosts[1:]
    return level.ghosts[0]


@pytest.fixture
def chase_setup(write_config: Callable[[str], str]
                ) -> Callable[..., tuple[Level, Ghost, list[list[int]]]]:
    """Returns a helper placing one ghost and the player on open cells."""

    def _build(ghost_pos: tuple[int, int] = (7, 0),
               player_pos: tuple[int, int] = (7, 7),
               difficulty: str = "Normal"
               ) -> tuple[Level, Ghost, list[list[int]]]:
        Config.load_from_file(
            write_config(f'{{"ghost_chase": "{difficulty}"}}'))
        grid = open_grid(15, 15)
        maze = Maze(grid)
        level = Level(maze)
        GameState.level = level
        ghost = _lone_ghost(level)
        level.player.cell = maze.get_cell(player_pos)
        ghost.cell = maze.get_cell(ghost_pos)
        return level, ghost, grid

    return _build


ChaseSetup = Callable[..., tuple[Level, Ghost, list[list[int]]]]


def test_ghosts_start_on_their_own_corner(
        open_level: Callable[..., Level]) -> None:
    """Four ghosts, four different corners."""

    level = open_level()

    assert all(ghost.cell is ghost.spawn for ghost in level.ghosts)
    assert {ghost.spawn.pos for ghost in level.ghosts} == {
        (0, 0), (14, 0), (0, 14), (14, 14)}


def test_a_chasing_ghost_closes_in_on_the_player(
        chase_setup: ChaseSetup) -> None:
    """One tick of chase shortens the distance to the player."""

    level, ghost, grid = chase_setup()
    target = level.player.cell.pos
    before = distance(grid, ghost.cell.pos, target)

    ghost.tick()

    assert distance(grid, ghost.cell.pos, target) < before


def test_a_normal_ghost_closes_in_to_touching_distance(
        chase_setup: ChaseSetup) -> None:
    """Chasing is not a random walk: it ends up next to the player.

    Planning three moves ahead on a straight-line distance leaves the
    ghost circling its target rather than landing on it.
    """

    level, ghost, grid = chase_setup(ghost_pos=(0, 0))
    target = level.player.cell.pos
    closest = distance(grid, ghost.cell.pos, target)

    for _ in range(40):
        ghost.tick()
        closest = min(closest, distance(grid, ghost.cell.pos, target))

    assert closest <= 1


def test_a_hardcore_ghost_lands_on_the_player(
        chase_setup: ChaseSetup) -> None:
    """The shortest path is walked one cell per tick, to the end."""

    level, ghost, grid = chase_setup(ghost_pos=(0, 0),
                                     difficulty="Hardcore")
    target = level.player.cell
    needed = distance(grid, ghost.cell.pos, target.pos)

    for _ in range(needed):
        ghost.tick()

    assert ghost.cell is target


def test_a_frightened_ghost_backs_away(
        chase_setup: ChaseSetup) -> None:
    """A ghost with room to run increases the distance."""

    level, ghost, grid = chase_setup(ghost_pos=(7, 5))
    ghost.frighten()
    target = level.player.cell.pos
    before = distance(grid, ghost.cell.pos, target)

    ghost.tick()

    assert distance(grid, ghost.cell.pos, target) > before


def test_a_chasing_ghost_cannot_be_eaten(
        open_level: Callable[..., Level]) -> None:
    """Eating a ghost that is not frightened is refused."""

    level = open_level()

    with pytest.raises(NotEdibleError):
        level.ghosts[0].eat()


def test_eating_a_frightened_ghost_scores_its_points(
        open_level: Callable[..., Level]) -> None:
    """A frightened ghost pays the configured prize and dies."""

    level = open_level()
    ghost = level.ghosts[0]
    ghost.frighten()

    assert ghost.eat() == Config.ghost_points
    assert ghost.mode is Ghost.GhostMode.DEAD


def test_a_dead_ghost_cannot_be_eaten_again(
        open_level: Callable[..., Level]) -> None:
    """One frightened ghost pays once."""

    level = open_level()
    ghost = level.ghosts[0]
    ghost.frighten()
    ghost.eat()

    with pytest.raises(NotEdibleError):
        ghost.eat()


def test_a_dead_ghost_leaves_the_maze(
        chase_setup: ChaseSetup) -> None:
    """An eaten ghost is off the grid, so it touches nobody."""

    level, ghost, grid = chase_setup(ghost_pos=(7, 7))
    ghost.frighten()
    ghost.eat()

    assert ghost.cell not in level.maze.cell_dict.values()
    assert not level.player.collides(ghost)


@known_bug("a DEAD ghost keeps can_collide, only its cell takes it away")
def test_a_dead_ghost_cannot_hurt_the_player(
        chase_setup: ChaseSetup) -> None:
    """A ghost waiting to respawn is out of play wherever it stands."""

    level, ghost, grid = chase_setup()
    ghost.frighten()
    ghost.eat()
    ghost.cell = level.player.cell

    assert not level.player.collides(ghost)


def test_a_frightened_ghost_calms_down_after_its_cooldown(
        chase_setup: ChaseSetup) -> None:
    """The edible state expires on its own."""

    level, ghost, grid = chase_setup(ghost_pos=(0, 0))
    ghost.frighten()

    for _ in range(Config.to_ticks(Config.ghost_edible_cooldown) + 1):
        ghost.tick()

    assert ghost.mode is Ghost.GhostMode.CHASE
    assert not ghost.edible


def test_a_dead_ghost_comes_back_home_after_its_cooldown(
        chase_setup: ChaseSetup) -> None:
    """An eaten ghost respawns on its corner, chasing again."""

    level, ghost, grid = chase_setup()
    home = ghost.spawn
    ghost.frighten()
    ghost.eat()

    for _ in range(Config.to_ticks(Config.ghost_cooldown) + 1):
        ghost.tick()

    assert ghost.mode is Ghost.GhostMode.CHASE
    assert ghost.cell is home


def test_a_ghost_only_walks_one_cell_per_tick(
        chase_setup: ChaseSetup) -> None:
    """A tick is a single step, whatever the difficulty."""

    level, ghost, grid = chase_setup(ghost_pos=(1, 1))

    for _ in range(10):
        before = ghost.cell.pos
        ghost.tick()
        assert distance(grid, before, ghost.cell.pos) <= 1
