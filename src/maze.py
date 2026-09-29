from . import CellNotFoundError, Config
from enum import Enum
from typing_extensions import overload
from typing import Self, Generator


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
        """Returns the horizontal increment."""

        return self.value[0]

    @property
    def y(self) -> int:
        """Returns the vertical increment."""

        return self.value[1]

    def apply(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Returns the movement increment in two dimensions."""

        return (pos[0] + self.x, pos[1] + self.y)


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

    @property
    def pos(self) -> tuple[int, int]:
        """Returns the two-dimensional position of the cell."""

        return (self.x, self.y)

    @property
    def accessible(self) -> bool:
        return self.walls != sum(Cell._WALL_BITS.values())

    def can_move(self, direction: Direction) -> bool:
        """Return whether the direction can be taken.

        direction -- The direction you want to take
        """

        return self.walls & Cell._WALL_BITS[direction] != 0

    @property
    def available_directions(self) -> list[Direction]:
        """Return the directions that can be taken from the cell."""

        return [direction
                for direction in Cell._WALL_BITS
                if not self.can_move(direction)
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
    cells -- The map of columns and rows of cell
    cell_dict -- A fast way to fetch cell from cell pos
    spawn -- All the spawnable cells for ghosts
    """

    width: int
    height: int
    cells: list[list[Cell]]
    cell_dict: dict[tuple[int, int], Cell]
    spawns: list[Cell]

    def __init__(self, grid: list[list[int]]) -> None:
        """Build the cells from a cell grid.

        grid -- The cell grid stored as column then row
        """

        self.cells = [[Cell(row_idx, column, wall)
                       for column, wall in enumerate(row)
                       ]
                      for row_idx, row in enumerate(grid)
                      ]
        self.cell_dict: dict[tuple[int, int], Cell] = {}
        self.height = len(grid)
        self.width = len(grid[0]) if self.height else 0

        for y, row in enumerate(grid):
            self.cells.append([])
            for x, wall in enumerate(row):
                cell: Cell = Cell(y, x, wall)
                self.cells[y].append(cell)
                self.cell_dict[(y, x)] = cell

        if Config.ghost_spawn == Config.GhostSpawnType.CLOSED_CELL:
            for cell in np.nditer(self.cells):
                if not cell.accessible:
                    self.spawns.append(cell)
        elif Config.ghost_spawn == Config.GhostSpawnType.CORNERS:
            self.spawns.append(self.cell_dict[(0, 0)])
            self.spawns.append(self.cell_dict[(0, self.height)])
            self.spawns.append(self.cell_dict[(self.width, 0)])
            self.spawns.append(self.cell_dict[(self.width, self.height)])

    def get_spawn(self, spawn_number: int) -> Cell:
        """Returns one of the spawn cells.

        spawn_number -- The id to which to refer to get one of the spawn cell

        Raises CellNotFoundError if no spawn cells are set
        """

        if not self.spawns:
            raise CellNotFoundError

        return self.spawns[spawn_number % len(self.spawns)]

    def inside_maze(self, x: int, y: int) -> bool:
        """Returns whether cell lies within the maze.

        x -- The x coordinate of the cell
        y -- The y coordinate of the cell

        """

        return self.get_cell(x, y) is not None

    @overload
    def get_cell(self, x: int, y: int) -> Cell:
        """Returns the cell corresponding to the x and y coordinates.

        x -- The x coordinate of the cell
        y -- The y coordinate of the cell

        Raises CellNotFoundError when the cell is outside the maze
        """

        try:
            return self.cell_dict[(x, y)]
        except IndexError:
            raise CellNotFoundError from None

    @overload
    def get_cell(self, pos: tuple[int, int]) -> Cell:
        """Returns the cell corresponding to the position.

        pos -- The two-dimensional coordinates of the cell

        Raises CellNotFoundError when the cell is outside the maze
        """

        try:
            return self.cell_dict[pos]
        except IndexError:
            raise CellNotFoundError from None

    def get_neighbor(self, cell: Cell, direction: Direction) -> Cell:
        """Returns the cell accessible from the direction.

        Loops around the map if it gets to an edge

        cell -- The cell departed from
        direction -- The direction taken

        Raises CellBlockedError if the cell is not accessible
        """

        return self.get_cell(direction.apply(cell.pos))

    def neighbors(self, cell: Cell) -> Generator[Cell, None, None]:
        """Returns all the cells reachable from one cell.

        cell -- The cell from which to fetch the neighbors
        """

        for direction in Direction:
            if direction == Direction.STILL:
                continue
            try:
                yield self.get_neighbor(cell, direction)
            except CellNotFoundError:
                continue

    def edge_direction(self, cell: Cell) -> Direction:
        """Returns the direction of the edge of the map of a cell.

        cell -- The cell to fetch if it is close to an edge of the map

        Returns Direction.STILL if the cell is not on an edge
        """

        return Direction((int(cell.y == self.height) - int(cell.y == 0),
                          int(cell.x == self.width) - int(cell.x == 0)))
