from __future__ import annotations

from enum import Enum
from functools import singledispatchmethod
from typing import Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from . import Entity

from . import CellNotFoundError, Config


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
    entities -- The entities currently on the cell
    """

    x: int
    y: int
    walls: int
    entities: list[Entity]

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
        self.entities = []

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

        if direction == Direction.STILL:
            return (False)
        return (self.walls & Cell._WALL_BITS[direction]) == 0

    @property
    def available_directions(self) -> list[Direction]:
        """Return the directions that can be taken from the cell."""

        return [direction
                for direction in Cell._WALL_BITS
                if self.can_move(direction)
                ]

    def __hash__(self) -> int:
        """Hashes the cell."""

        return hash((self.x, self.y))

    def __eq__(self, other: object) -> bool:
        """Returns if the cell is the same as the given one.

        other -- The object  to compare this cell to
        """

        if not isinstance(other, Cell):
            return False
        return bool(self.x == other.x and self.y == other.y)

    def update(self, delta_time: int) -> None:
        # TODO: draw cell
        pass


class Maze:
    """Grid of cells, built once per level.

    width -- The number of columns
    height -- The number of rows
    cell_dict -- A fast way to fetch cell from cell pos
    spawn -- All the spawnable cells for ghosts
    get_center -- Returns the accessible cell closest to the middle
    """

    width: int
    height: int
    cell_dict: dict[tuple[int, int], Cell]
    corners: list[Cell]
    spawns: list[Cell]

    def __init__(self, grid: list[list[int]]) -> None:
        """Build the cells from a cell grid.

        grid -- The cell grid stored as column then row
        """

        self.cell_dict = {}
        self.spawns = []
        self.corners = []
        self.height = len(grid)
        self.width = len(grid[0]) if self.height else 0

        for y, row in enumerate(grid):
            for x, wall in enumerate(row):
                cell: Cell = Cell(x, y, wall)
                self.cell_dict[(x, y)] = cell

        self.corners.append(self.cell_dict[(0, 0)])
        self.corners.append(self.cell_dict[(0, self.height - 1)])
        self.corners.append(self.cell_dict[(self.width - 1, 0)])
        self.corners.append(self.cell_dict[(self.width - 1, self.height - 1)])

        if Config.ghost_spawn == Config.GhostSpawnType.CLOSED_CELL:
            for cell in self.cell_dict.values():
                if not cell.accessible:
                    self.spawns.append(cell)
        elif Config.ghost_spawn == Config.GhostSpawnType.CORNERS:
            self.spawns += self.corners

    def get_center(self) -> Cell:
        """Returns the accessible cell closest to the middle of the maze."""

        middle: tuple[int, int] = (self.width // 2, self.height // 2)
        return min((cell for cell in self.cell_dict.values()
                    if cell.accessible),
                   key=lambda cell: (abs(cell.x - middle[0])
                                     + abs(cell.y - middle[1])))

    def get_spawn(self, spawn_number: int) -> Cell:
        """Returns one of the spawn cells.

        spawn_number -- The id to which to refer to get one of the spawn cell

        Raises CellNotFoundError if no spawn cells are set
        """

        if not self.spawns:
            raise CellNotFoundError("Spawn")
        return self.spawns[spawn_number % len(self.spawns)]

    def inside_maze(self, x: int, y: int) -> bool:
        """Returns whether cell lies within the maze.

        x -- The x coordinate of the cell
        y -- The y coordinate of the cell

        """

        try:
            self.get_cell(x, y)
            return True
        except CellNotFoundError:
            return False

    @singledispatchmethod
    def get_cell(self, first: int | tuple[int, int], second: int) -> Cell:
        """Returns the cell corresponding to the x and y coordinates.

        first -- The x coordinate of the cell or x,y pair
        second -- The y coordinate of the cell

        Raises CellNotFoundError when the cell is outside the maze
        """
        raise ValueError(f"Wrong arguments [{first}, {second}]")

    @get_cell.register(int)
    def _(self, x: int, y: int) -> Cell:
        """Returns the cell corresponding to the x and y coordinates.

        x -- The x coordinate of the cell
        y -- The y coordinate of the cell

        Raises CellNotFoundError when the cell is outside the maze
        """

        try:
            return self.cell_dict[(x, y)]
        except KeyError:
            raise CellNotFoundError((x, y)) from None

    @get_cell.register(tuple)
    def _(self, pos: tuple[int, int]) -> Cell:
        """Returns the cell corresponding to the position.

        pos -- The two-dimensional coordinates of the cell

        Raises CellNotFoundError when the cell is outside the maze
        """

        try:
            return self.cell_dict[pos]
        except KeyError:
            raise CellNotFoundError(pos) from None

    def get_neighbor(self, cell: Cell, direction: Direction) -> Cell:
        """Returns the cell next to a cell toward a direction.

        Leaving the grid by one edge comes back on the opposite edge.
        cell -- The cell departed from
        direction -- The direction taken
        """

        x, y = direction.apply(cell.pos)
        return self.get_cell((x % self.width, y % self.height))

    def neighbors(self, cell: Cell) -> Generator[Cell, None, None]:
        """Returns all the cells reachable from one cell.

        cell -- The cell from which to fetch the neighbors
        """

        for direction in Direction:
            if direction == Direction.STILL or not cell.can_move(direction):
                continue
            try:
                yield self.get_neighbor(cell, direction)
            except CellNotFoundError:
                continue

    def edge_direction(self, cell: Cell) -> Direction:
        """Returns the direction of the edge of the map of a cell.

        cell -- The cell to fetch if it is close to an edge of the map

        Returns Direction.STILL if the cell is not on an edge
            or the left or right edge for a corner
        """

        horizontal: int = int(cell.x == self.width - 1) - int(cell.x == 0)
        vertical: int = int(cell.y == self.height - 1) - int(cell.y == 0)
        return Direction((horizontal, 0) if horizontal else (0, vertical))

    def update(self, delta_time: int) -> None:
        """Draws the whole maze.

        delta_time -- The time inbetween two frames
        """

        for cell in self.cell_dict.values():
            cell.update(delta_time)
