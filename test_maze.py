"""The maze layer hides the generator's wall bits behind cells."""

import pytest

from src import CellNotFoundError, Direction, Ghost, Maze, Player

from helpers import close_passage, distance, open_edges, open_grid, seal_cell
from review import verifies


@verifies("src.maze.Maze.__init__")
def test_size_matches_the_grid() -> None:
    """A grid of rows of columns keeps its dimensions."""

    maze = Maze(open_grid(9, 5))

    assert maze.width == 9
    assert maze.height == 5


@verifies("src.maze.Maze.get_cell")
def test_cells_are_indexed_by_x_then_y() -> None:
    """Both call shapes reach the same cell object."""

    maze = Maze(open_grid(9, 5))
    cell = maze.get_cell(7, 3)

    assert cell.pos == (7, 3)
    assert maze.get_cell((7, 3)) is cell


@verifies("src.maze.Maze.get_cell")
def test_a_cell_outside_the_maze_raises() -> None:
    """Asking outside the grid raises instead of returning None."""

    maze = Maze(open_grid(5, 5))

    with pytest.raises(CellNotFoundError):
        maze.get_cell(5, 5)


@verifies("src.maze.Maze.inside_maze")
def test_a_cell_outside_the_maze_is_reported() -> None:
    """inside_maze answers instead of raising."""

    maze = Maze(open_grid(5, 5))

    assert maze.inside_maze(4, 4)
    assert not maze.inside_maze(5, 5)


@verifies("src.maze.Maze.neighbors")
def test_an_inner_cell_has_four_neighbors() -> None:
    """Without inner walls every side leads somewhere."""

    maze = Maze(open_grid(5, 5))

    assert {cell.pos for cell in maze.neighbors(maze.get_cell(2, 2))} == {
        (2, 1), (3, 2), (2, 3), (1, 2)}


@verifies("src.maze.Cell.available_directions")
def test_an_inner_cell_opens_on_four_sides() -> None:
    """Without inner walls every direction is available."""

    maze = Maze(open_grid(5, 5))

    assert set(maze.get_cell(2, 2).available_directions) == {
        Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT}


@verifies("src.maze.Cell.available_directions")
def test_a_corner_cell_only_opens_inwards() -> None:
    """The outer border closes two sides of a corner."""

    maze = Maze(open_grid(5, 5))

    assert set(maze.get_cell(0, 0).available_directions) == {
        Direction.RIGHT, Direction.DOWN}


@verifies("src.maze.Maze.neighbors")
def test_neighbors_stop_at_a_closed_passage() -> None:
    """A wall removes the cell behind it from the neighbours."""

    grid = open_grid(5, 5)
    close_passage(grid, 2, 2, Direction.RIGHT)
    maze = Maze(grid)
    cell = maze.get_cell(2, 2)

    assert not cell.can_move(Direction.RIGHT)
    assert (3, 2) not in {neighbour.pos for neighbour in maze.neighbors(cell)}


@verifies("src.maze.Maze.neighbors")
def test_a_corner_has_two_neighbors() -> None:
    """The outer border closes two sides of a corner."""

    maze = Maze(open_grid(5, 5))

    assert {cell.pos for cell in maze.neighbors(maze.get_cell(0, 0))} == {
        (1, 0), (0, 1)}


@verifies("src.maze.Cell.can_move")
def test_standing_still_is_answered_without_raising() -> None:
    """Direction.STILL is refused, not rejected with a KeyError."""

    cell = Maze(open_grid(5, 5)).get_cell(2, 2)

    assert not cell.can_move(Direction.STILL)


@verifies("src.maze.Cell.accessible")
def test_a_sealed_cell_is_not_accessible() -> None:
    """A cell walled on four sides is the '42' pattern, not a corridor."""

    grid = open_grid(5, 5)
    seal_cell(grid, 2, 2)
    maze = Maze(grid)

    assert not maze.get_cell(2, 2).accessible
    assert maze.get_cell(1, 1).accessible


@verifies("src.maze.Cell.__init__")
def test_a_fresh_cell_holds_no_entity() -> None:
    """A maze is built empty, the level fills it."""

    maze = Maze(open_grid(5, 5))

    assert all(cell.entities == [] for cell in maze.cell_dict.values())


@verifies("src.maze.Maze.__init__")
def test_the_corners_are_the_four_corner_cells() -> None:
    """The corners are where the super pacgums and the ghosts go."""

    maze = Maze(open_grid(7, 5))

    assert {cell.pos for cell in maze.corners} == {(0, 0), (6, 0),
                                                   (0, 4), (6, 4)}


@verifies("src.maze.Maze.get_spawn")
def test_corner_spawns_are_the_four_corners() -> None:
    """Ghosts are given one corner each."""

    maze = Maze(open_grid(7, 5))

    assert {cell.pos for cell in maze.spawns} == {(0, 0), (6, 0),
                                                  (0, 4), (6, 4)}
    assert len({maze.get_spawn(i).pos for i in range(4)}) == 4


@verifies("src.maze.Maze.get_spawn")
def test_spawns_cycle_past_their_count() -> None:
    """More ghosts than corners reuse the corners instead of failing."""

    maze = Maze(open_grid(7, 5))

    assert maze.get_spawn(4) is maze.get_spawn(0)


@verifies("src.maze.Maze.edge_direction")
def test_an_edge_cell_reports_its_side() -> None:
    """A cell against one border names that border."""

    maze = Maze(open_grid(7, 5))

    assert maze.edge_direction(maze.get_cell(0, 3)) is Direction.LEFT
    assert maze.edge_direction(maze.get_cell(6, 3)) is Direction.RIGHT


@verifies("src.maze.Maze.edge_direction")
def test_an_inner_cell_reports_no_side() -> None:
    """A cell away from the border is on no edge."""

    maze = Maze(open_grid(7, 5))

    assert maze.edge_direction(maze.get_cell(3, 2)) is Direction.STILL


@verifies("src.maze.Maze.edge_direction")
def test_a_top_edge_cell_reports_up() -> None:
    """The top row is the UP edge, not the DOWN one."""

    maze = Maze(open_grid(7, 5))

    assert maze.edge_direction(maze.get_cell(3, 0)) is Direction.UP


@verifies("src.maze.Maze.edge_direction")
def test_a_corner_cell_reports_one_side() -> None:
    """A corner touches two borders and must still answer."""

    maze = Maze(open_grid(7, 5))

    assert maze.edge_direction(maze.get_cell(0, 0)) is Direction.LEFT
    assert maze.edge_direction(maze.get_cell(6, 4)) is Direction.RIGHT


@verifies("src.maze.Maze.get_center")
def test_the_center_is_the_middle_cell() -> None:
    """The player spawn sits in the middle of an open maze."""

    maze = Maze(open_grid(15, 15))

    assert maze.get_center().pos == (7, 7)


@verifies("src.maze.Maze.get_center")
def test_a_sealed_middle_moves_the_center_to_the_closest_open_cell() -> None:
    """The player never spawns inside the '42' pattern."""

    grid = open_grid(15, 15)
    seal_cell(grid, 7, 7)

    assert Maze(grid).get_center().pos in {(7, 6), (6, 7), (8, 7), (7, 8)}


@verifies("src.entities.Ghost.can_move")
def test_only_a_ghost_leaves_a_sealed_cell() -> None:
    """A ghost ignores the walls of a closed cell, the player does not."""

    grid = open_grid(5, 5)
    seal_cell(grid, 2, 2)
    maze = Maze(grid)
    sealed = maze.get_cell(2, 2)
    ghost = Ghost(sealed, 0)
    player = Player(sealed)
    sides = (Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT)

    assert all(ghost.can_move(sealed, direction) for direction in sides)
    assert not any(player.can_move(sealed, direction) for direction in sides)
    assert not ghost.can_move(maze.get_cell(2, 1), Direction.DOWN)


@verifies("src.maze.Maze.get_neighbor")
def test_leaving_by_an_open_edge_comes_back_on_the_other_side() -> None:
    """An open border is a tunnel, as in the arcade game."""

    maze = Maze(open_edges(open_grid(7, 5)))

    assert maze.get_neighbor(maze.get_cell(0, 3),
                             Direction.LEFT).pos == (6, 3)
    assert maze.get_neighbor(maze.get_cell(2, 0),
                             Direction.UP).pos == (2, 4)


@verifies("src.maze.Cell.can_move")
def test_a_closed_edge_is_still_a_wall() -> None:
    """A maze with its border intact has no tunnel."""

    maze = Maze(open_grid(7, 5))

    assert not maze.get_cell(0, 3).can_move(Direction.LEFT)


def test_the_helper_distance_matches_the_maze_walls() -> None:
    """The validator used by the other tests reads the walls correctly."""

    grid = open_grid(10, 1)

    assert distance(grid, (0, 0), (6, 0)) == 6
    assert distance(grid, (4, 0), (4, 0)) == 0


def test_the_helper_distance_reports_an_unreachable_cell() -> None:
    """A cut corridor gives the unreachable sentinel."""

    grid = open_grid(4, 1)
    close_passage(grid, 1, 0, Direction.RIGHT)

    assert distance(grid, (0, 0), (3, 0)) == -1
