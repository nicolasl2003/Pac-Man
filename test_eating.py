"""The player eats what it steps on, and a ghost it meets costs a life.

Every collision is resolved by Player.move, so a still player is only
caught when it calls move again. The tests run on every config variant.
"""

from typing import Callable

from src import Cell, Config, Direction, GameState, Ghost, Level, PacGum
from src import SuperPacGum

from gaps import known_bug


def _plain_gum(level: Level) -> PacGum:
    """Returns a pacgum that is not a super one.

    level -- the level to search
    """

    return next(gum for gum in level.pacgums
                if not isinstance(gum, SuperPacGum))


def _corner_super_gum(level: Level) -> SuperPacGum:
    """Returns a super pacgum, which the level lays in a corner.

    level -- the level to search
    """

    return next(gum for gum in level.pacgums
                if isinstance(gum, SuperPacGum))


def _park_ghosts(level: Level, away_from: Cell) -> None:
    """Sends every ghost to the cell the furthest from another one.

    level -- the level whose ghosts are moved
    away_from -- the cell the ghosts must stay clear of
    """

    far: Cell = max(level.maze.cell_dict.values(),
                    key=lambda cell: (abs(cell.x - away_from.x)
                                      + abs(cell.y - away_from.y)))
    for ghost in level.ghosts:
        ghost.cell = far


def _step_onto(level: Level, target: Cell) -> None:
    """Puts the player on a side of a cell and makes it step onto it.

    level -- the level the player plays in
    target -- the cell to step onto
    """

    for step in (Direction.RIGHT, Direction.LEFT,
                 Direction.DOWN, Direction.UP):
        start = (target.x - step.x, target.y - step.y)
        if level.maze.inside_maze(*start):
            level.player.cell = level.maze.get_cell(*start)
            level.player.move(step)
            return
    raise AssertionError(f"{target.pos} has no neighbour to come from")


def _meet_a_ghost(level: Level) -> Ghost:
    """Puts a ghost one step above the player, away from any gum corner.

    level -- the level to play in
    Returns the ghost that was placed
    """

    ghost = level.ghosts[0]
    level.player.cell = level.maze.get_cell(7, 7)
    ghost.cell = level.maze.get_cell(7, 6)
    return ghost


def test_stepping_on_a_pacgum_eats_it(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """The pacgum leaves the level and the cell it was on."""

    level = open_level()
    gum = _plain_gum(level)
    _park_ghosts(level, gum.cell)

    _step_onto(level, gum.cell)

    assert gum not in level.pacgums
    assert gum not in gum.cell.entities
    assert level.player.cell is gum.cell


def test_a_pacgum_is_only_eaten_once(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """Staying on the cleared cell eats nothing more and raises nothing."""

    level = open_level()
    gum = _plain_gum(level)
    _park_ghosts(level, gum.cell)
    _step_onto(level, gum.cell)
    left = len(level.pacgums)

    level.player.move(Direction.STILL)

    assert len(level.pacgums) == left


def test_the_other_pacgums_are_left_alone(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """Eating one pacgum removes exactly one."""

    level = open_level()
    gum = _plain_gum(level)
    _park_ghosts(level, gum.cell)
    before = len(level.pacgums)

    _step_onto(level, gum.cell)

    assert len(level.pacgums) == before - 1


def test_stepping_on_a_super_pacgum_frightens_every_ghost(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """The power pellet turns all the ghosts edible, wherever they are."""

    level = open_level()
    gum = _corner_super_gum(level)
    _park_ghosts(level, gum.cell)

    _step_onto(level, gum.cell)

    assert gum not in level.pacgums
    assert level.ghosts
    assert all(ghost.mode is Ghost.GhostMode.EDIBLE and ghost.edible
               for ghost in level.ghosts)


def test_a_super_pacgum_without_ghosts_is_eaten_quietly(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """A level with no ghost has nobody to frighten, and must not fail."""

    Config.load_from_file(write_config('{"ghost_count": 0}'))
    level = open_level()
    gum = _corner_super_gum(level)

    _step_onto(level, gum.cell)

    assert gum not in level.pacgums


def test_stepping_on_a_frightened_ghost_eats_it(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """The ghost dies, and the player keeps its lives."""

    level = open_level()
    ghost = _meet_a_ghost(level)
    ghost.frighten()
    lives = GameState.lives

    level.player.move(Direction.UP)

    assert ghost.mode is Ghost.GhostMode.DEAD
    assert GameState.lives == lives
    assert level.player.cell.pos == (7, 6)


def test_stepping_on_a_calm_ghost_costs_a_life(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """A ghost that is not frightened hurts."""

    level = open_level()
    _meet_a_ghost(level)
    lives = GameState.lives

    level.player.move(Direction.UP)

    assert GameState.lives == lives - 1


def test_a_lost_life_sends_everyone_home(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """The player and every ghost stand on their spawn again."""

    level = open_level()
    _meet_a_ghost(level)
    GameState.lives = 2

    level.player.move(Direction.UP)

    assert level.player.cell is level.player.spawn
    assert all(ghost.cell is ghost.spawn for ghost in level.ghosts)
    assert level.state is Level.State.RUNNING


def test_a_blocked_move_still_meets_the_ghost_on_the_cell(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """Pushing into the border does not skip the collision check."""

    level = open_level()
    ghost = level.ghosts[0]
    level.player.cell = level.maze.get_cell(0, 5)
    ghost.cell = level.player.cell
    lives = GameState.lives

    level.player.move(Direction.LEFT)

    assert GameState.lives == lives - 1


def test_a_ghost_that_walks_onto_a_still_player_is_caught_on_the_next_move(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """Collisions are only resolved when the player moves, even in place."""

    level = open_level()
    level.player.cell = level.maze.get_cell(7, 7)
    level.ghosts[0].cell = level.player.cell
    lives = GameState.lives

    level.player.move(Direction.STILL)

    assert GameState.lives == lives - 1


@known_bug("eat() returns the prize, but Player.move drops it and nothing "
           "adds it to GameState.score")
def test_eating_a_pacgum_scores_its_points(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """The score grows by the prize of the config."""

    level = open_level()
    gum = _plain_gum(level)
    _park_ghosts(level, gum.cell)

    _step_onto(level, gum.cell)

    assert GameState.score == Config.pacgum_points


@known_bug("eat() returns the prize, but Player.move drops it and nothing "
           "adds it to GameState.score")
def test_eating_a_super_pacgum_scores_its_points(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """The power pellet pays its own prize."""

    level = open_level()
    gum = _corner_super_gum(level)
    _park_ghosts(level, gum.cell)

    _step_onto(level, gum.cell)

    assert GameState.score == Config.ss_pacgum_points


@known_bug("eat() returns the prize, but Player.move drops it and nothing "
           "adds it to GameState.score")
def test_eating_a_ghost_scores_its_points(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """A frightened ghost pays the ghost prize."""

    level = open_level()
    _meet_a_ghost(level).frighten()

    level.player.move(Direction.UP)

    assert GameState.score == Config.ghost_points


@known_bug("SuperPacGum.eat returns True where every other eat returns "
           "the prize")
def test_a_super_pacgum_eats_for_its_prize(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """The caller gets the points back from the eat call itself."""

    gum = _corner_super_gum(open_level())

    assert gum.eat() == Config.ss_pacgum_points


@known_bug("lose_life runs once for every ghost on the cell")
def test_two_ghosts_on_the_player_cost_a_single_life(
        open_level: Callable[..., Level]) -> None:
    """Being caught is one event, however many ghosts did it."""

    level = open_level()
    level.player.cell = level.maze.get_cell(7, 7)
    for ghost in level.ghosts[:2]:
        ghost.cell = level.maze.get_cell(7, 6)
    GameState.lives = 3

    level.player.move(Direction.UP)

    assert GameState.lives == 2


@known_bug("the collision loop keeps eating after the player lost a life")
def test_a_pacgum_under_a_killer_ghost_is_not_eaten(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """The player died on that cell, so it did not eat what lay there.

    A level opens with a ghost on every corner, and a super pacgum under it.
    """

    level = open_level()
    gum = _corner_super_gum(level)
    assert any(isinstance(entity, Ghost) for entity in gum.cell.entities)

    _step_onto(level, gum.cell)

    assert gum in level.pacgums
    assert level.player.cell is level.player.spawn


@known_bug("frighten wakes a DEAD ghost up in the maze, before its cooldown")
def test_a_super_pacgum_does_not_bring_a_dead_ghost_back(
        config_variant: str, open_level: Callable[..., Level]) -> None:
    """An eaten ghost waits for its own cooldown, whatever happens."""

    level = open_level()
    gum = _corner_super_gum(level)
    ghost = level.ghosts[0]
    ghost.frighten()
    ghost.eat()
    _park_ghosts(level, gum.cell)
    ghost.cell = Cell(-1, -1, 15)
    ghost.mode = Ghost.GhostMode.DEAD

    _step_onto(level, gum.cell)

    assert ghost.mode is Ghost.GhostMode.DEAD
