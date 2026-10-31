"""Entities move cell by cell and keep their cell bookkeeping in step."""

from typing import Callable

from src import Direction, GameState, Level, Maze, Rotation

from helpers import close_passage, open_edges, open_grid
from review import verifies


@verifies("src.entities.Rotation")
def test_rotation_has_four_distinct_values() -> None:
    """Four angles, not four aliases of the same member."""

    assert len(set(Rotation)) == 4


@verifies("src.entities.Rotation.from_direction")
def test_every_moving_direction_maps_to_a_rotation() -> None:
    """Turning sets the matching rotation."""

    rotations = {Rotation.from_direction(direction)
                 for direction in (Direction.UP, Direction.RIGHT,
                                   Direction.DOWN, Direction.LEFT)}

    assert len(rotations) == 4


@verifies("src.entities.MovingEntity.update_rotation")
def test_standing_still_keeps_the_last_rotation(
        open_level: Callable[..., Level]) -> None:
    """A stopped entity does not snap back to a default angle."""

    player = open_level().player
    before = player.rotation
    player.direction = Direction.UP
    turned = player.rotation
    player.direction = Direction.STILL

    assert turned is not before
    assert player.rotation is turned


@verifies("src.entities.MovingEntity.move")
def test_an_entity_follows_its_direction(
        open_level: Callable[..., Level]) -> None:
    """One move crosses exactly one cell."""

    level = open_level()
    player = level.player
    x, y = player.cell.pos

    player.move(Direction.RIGHT)

    assert player.cell.pos == (x + 1, y)


@verifies("src.entities.MovingEntity.move")
def test_a_move_records_its_direction(
        open_level: Callable[..., Level]) -> None:
    """The entity keeps facing where it was last sent."""

    player = open_level().player

    player.move(Direction.DOWN)

    assert player.direction is Direction.DOWN


@verifies("src.entities.MovingEntity.move")
def test_a_wall_blocks_the_move() -> None:
    """A move into a wall changes nothing."""

    grid = open_grid(5, 5)
    close_passage(grid, 2, 2, Direction.RIGHT)
    maze = Maze(grid)
    level = Level(maze)
    GameState.level = level
    level.player.cell = maze.get_cell(2, 2)

    level.player.move(Direction.RIGHT)

    assert level.player.cell.pos == (2, 2)


@verifies("src.entities.MovingEntity.move")
def test_a_blocked_move_still_records_its_direction() -> None:
    """Pushing into a wall turns the entity without moving it."""

    grid = open_grid(5, 5)
    close_passage(grid, 2, 2, Direction.RIGHT)
    maze = Maze(grid)
    level = Level(maze)
    GameState.level = level
    level.player.cell = maze.get_cell(2, 2)

    level.player.move(Direction.RIGHT)

    assert level.player.direction is Direction.RIGHT


@verifies("src.entities.MovingEntity.move")
def test_the_border_blocks_the_move(
        open_level: Callable[..., Level]) -> None:
    """Leaving the maze is refused, it does not raise."""

    level = open_level()
    level.player.cell = level.maze.get_cell(0, 5)

    level.player.move(Direction.LEFT)

    assert level.player.cell.pos == (0, 5)


@verifies("src.entities.MovingEntity.move")
def test_standing_still_is_not_a_move(
        open_level: Callable[..., Level]) -> None:
    """Direction.STILL leaves the entity where it is, without raising."""

    level = open_level()
    before = level.player.cell

    level.player.move(Direction.STILL)

    assert level.player.cell is before


@verifies("src.entities.RenderedEntity.__setattr__")
def test_the_screen_position_follows_the_cell(
        open_level: Callable[..., Level]) -> None:
    """Assigning a cell keeps the drawing coordinates in step."""

    level = open_level()
    level.player.cell = level.maze.get_cell(3, 4)

    assert (level.player.x, level.player.y) == (3, 4)


@verifies("src.entities.Entity.__setattr__")
def test_an_entity_registers_on_its_cell(
        open_level: Callable[..., Level]) -> None:
    """The cell knows what stands on it, once."""

    level = open_level()
    player = level.player

    assert player in player.cell.entities
    assert player.cell.entities.count(player) == 1


@verifies("src.entities.MovingEntity.move")
def test_moving_leaves_the_previous_cell(
        open_level: Callable[..., Level]) -> None:
    """An entity is listed on one cell at a time."""

    level = open_level()
    player = level.player
    left = player.cell

    player.move(Direction.RIGHT)

    assert player not in left.entities
    assert player in player.cell.entities


@verifies("src.entities.Entity.respawn")
def test_respawning_returns_to_the_spawn_cell(
        open_level: Callable[..., Level]) -> None:
    """An entity sent home stands on its spawn again."""

    level = open_level()
    ghost = level.ghosts[0]
    ghost.cell = level.maze.get_cell(5, 5)
    ghost.respawn()

    assert ghost.cell is ghost.spawn
    assert ghost in ghost.spawn.entities


@verifies("src.entities.MovingEntity.collides")
def test_two_entities_on_one_cell_collide(
        open_level: Callable[..., Level]) -> None:
    """Collision is decided by the cell, not by the pixels."""

    level = open_level()
    ghost = level.ghosts[0]
    ghost.cell = level.player.cell

    assert level.player.collides(ghost)
    assert ghost.collides(level.player)


@verifies("src.entities.MovingEntity.collides")
def test_entities_on_different_cells_do_not_collide(
        open_level: Callable[..., Level]) -> None:
    """Neighbouring entities are not touching."""

    level = open_level()
    ghost = level.ghosts[0]
    ghost.cell = level.maze.get_cell(0, 0)
    level.player.cell = level.maze.get_cell(5, 5)

    assert not level.player.collides(ghost)


@verifies("src.entities.MovingEntity.collides")
def test_an_entity_that_cannot_collide_is_out_of_play(
        open_level: Callable[..., Level]) -> None:
    """A ghost waiting to respawn is not a collision."""

    level = open_level()
    ghost = level.ghosts[0]
    ghost.cell = level.player.cell
    ghost.can_collide = False

    assert not level.player.collides(ghost)
    assert not ghost.collides(level.player)


@verifies("src.player.Player.get_collisions")
def test_the_player_lists_what_it_stands_on(
        open_level: Callable[..., Level]) -> None:
    """get_collisions reports the ghost sharing the cell."""

    level = open_level()
    ghost = level.ghosts[0]
    ghost.cell = level.player.cell

    assert ghost in level.player.get_collisions()


@verifies("src.player.Player.get_collisions")
def test_the_player_does_not_collide_with_itself(
        open_level: Callable[..., Level]) -> None:
    """The player stands on its own cell and must be skipped."""

    level = open_level()

    assert level.player not in level.player.get_collisions()


@verifies("src.player.Player.move")
def test_the_player_walks_through_an_open_edge() -> None:
    """Leaving the maze on one side lands on the other."""

    maze = Maze(open_edges(open_grid(9, 9)))
    level = Level(maze)
    GameState.level = level
    level.player.cell = maze.get_cell(0, 4)

    level.player.move(Direction.LEFT)

    assert level.player.cell.pos == (8, 4)


@verifies("src.entities.Ghost.can_move")
def test_a_ghost_walks_through_an_open_edge() -> None:
    """Ghosts use the same tunnels as the player."""

    maze = Maze(open_edges(open_grid(9, 9)))
    level = Level(maze)
    GameState.level = level
    ghost = level.ghosts[0]
    ghost.cell = maze.get_cell(4, 0)

    ghost.move(Direction.UP)

    assert ghost.cell.pos == (4, 8)
