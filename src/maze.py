from . import CellNotFoundError
from enum import Enum
from typings import Self


class Direction(Enum):
    """The direction an entity can take.

    UP -- The up direction
    RIGHT -- The right direction
    DOWN -- The down direction
    LEFT -- The left direction
    """

    STILL = (0, 0)
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)

    @property
    def x(self) -> int:
        """Return the horizontal step."""
        return self.value[0]

    @property
    def y(self) -> int:
        """Return the vertical step."""
        return self.value[1]


class Cell:
    """The cell class of the maze.

    x -- The cell column index
    y -- The cell row index
    walls -- The cell walls
    """

    x: int
    y: int
    walls: int

    _WALL_BITS = {
        Direction.UP: 1,
        Direction.RIGHT: 2,
        Direction.DOWN: 4,
        Direction.LEFT: 8,
    }

    def __init__(self, x: int, y: int, walls: int) -> None:
        """Build the cell from coordinated and wall state.

        x -- The x coordinate of the cell
        y -- The y coordinate of the cell
        walls -- The wall state of the cell
        """

        self.x = x
        self.y = y
        self.walls = walls

    def is_blocked(self, direction: Direction) -> bool:
        """Return whether the direction can be taken.

        direction -- The direction you want to take
        """

        return self.walls & Cell._WALL_BITS[direction] != 0

    def available_directions(self) -> list[Direction]:
        """Return the directions that can be taken from the cell."""

        return [direction
                for direction in Cell._WALL_BITS
                if not self.is_blocked(direction)
                ]

    def __hash__(self) -> int:
        """Hashes the cell."""

        return hash((self.x, self.y))

    def __eq__(self, other: Self) -> bool:
        """Returns if the cell is the same as the given one.

        other -- The cell to compare this cell to
        """

        return bool(self.x == other.x and self.y == other.y)


class Maze:
    """Grid of cells, built once per level.

    width -- The number of columns
    height -- The number of rows
    cells -- The list of list of maze cell
    """

    def __init__(self, grid: list[list[int]]) -> None:
        """Build the cells from a cell grid.

        grid -- The cell grid as int stored as column then row
        """
        # TODO: build the cell list as [y][x]
        self.cells: list[list[Cell]] = []
        self.width = 0
        self.height = 0

    def inside_maze(self, x: int, y: int) -> bool:
        """Returns whether (x, y) lies within the maze.

        x -- The x coordinate of the cell
        y -- The y coordinate of the cell

        """

        return self.get_cell(x, y) is not None

    def get_cell(self, x: int, y: int) -> Cell:
        """Returns the cell corresponding to the x and y coordinates.

        x -- The x coordinate of the cell
        y -- The y coordinate of the cell

        Raises CellNotFoundError when the cell is outside of the maze
        """
        try:
            return self.cells[y][x]
        except IndexError:
            raise CellNotFoundError from None

    def get_neighbor(self, cell: Cell, direction: Direction) -> Cell:
        """Returns the cell accessible from the direction.

        Loops around the map if it gets to an edge

        cell -- The cell departed from
        direction -- The direction taken

        Raises CellBlockedError if the cell is not accessible
        """
        raise NotImplementedError  # TODO

    def neighbors(self, cell: Cell) -> list[Cell]:
        """Returns all the cells reachable from one cell.

        cell -- The cell from which to fetch the neighbors
        """
        raise NotImplementedError  # TODO

    def edge_direction(self) -> Direction:
        """Returns the direction of the edge of the map of a cell.

        Returns Direction.STILL if the cell is not on an edge
        """
        raise NotImplementedError  # TODO
