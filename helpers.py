"""Hand-made grids, so the tests never depend on the maze generator."""

from collections import deque
from pathlib import Path

from src import Direction

ROOT = Path(__file__).resolve().parent.parent


def open_grid(width: int, height: int) -> list[list[int]]:
    """Returns a grid whose only walls are the outer border.

    width -- number of columns
    height -- number of rows
    """

    return [[(1 if y == 0 else 0)
             | (2 if x == width - 1 else 0)
             | (4 if y == height - 1 else 0)
             | (8 if x == 0 else 0)
             for x in range(width)
             ]
            for y in range(height)
            ]


def close_passage(grid: list[list[int]], x: int, y: int,
                  direction: Direction) -> None:
    """Raises a wall between a cell and its neighbour, on both sides.

    grid -- the grid to alter, indexed as grid[y][x]
    x -- column of the cell the wall is raised from
    y -- row of the cell the wall is raised from
    direction -- side of that cell the wall closes
    """

    bits = {Direction.UP: (1, 4), Direction.RIGHT: (2, 8),
            Direction.DOWN: (4, 1), Direction.LEFT: (8, 2)}
    bit, opposite = bits[direction]
    grid[y][x] |= bit
    neighbour_x, neighbour_y = x + direction.x, y + direction.y
    if 0 <= neighbour_y < len(grid) and 0 <= neighbour_x < len(grid[0]):
        grid[neighbour_y][neighbour_x] |= opposite


def seal_cell(grid: list[list[int]], x: int, y: int) -> None:
    """Walls a cell on its four sides, the way the '42' pattern does.

    grid -- the grid to alter, indexed as grid[y][x]
    x -- column of the cell to seal
    y -- row of the cell to seal
    """

    for direction in (Direction.UP, Direction.RIGHT,
                      Direction.DOWN, Direction.LEFT):
        close_passage(grid, x, y, direction)


def open_edges(grid: list[list[int]]) -> list[list[int]]:
    """Returns the same grid with its outer border opened, as a torus.

    grid -- the grid to open, indexed as grid[y][x]
    """

    height, width = len(grid), len(grid[0])
    return [[walls & ~((1 if y == 0 else 0)
                       | (2 if x == width - 1 else 0)
                       | (4 if y == height - 1 else 0)
                       | (8 if x == 0 else 0))
             for x, walls in enumerate(row)
             ]
            for y, row in enumerate(grid)
            ]


def manhattan(first: tuple[int, int], second: tuple[int, int]) -> int:
    """Returns the distance between two positions, walls ignored.

    first -- one position
    second -- the other position
    """

    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def distance(grid: list[list[int]], start: tuple[int, int],
             goal: tuple[int, int]) -> int:
    """Returns the number of moves from one position to another.

    The walls are read from the grid, so the maze code is never used.
    grid -- the grid to walk, indexed as grid[y][x]
    start -- the position departed from
    goal -- the position to reach
    Returns the move count
        or -1 when no path joins the two positions
    """

    bits = {(0, -1): 1, (1, 0): 2, (0, 1): 4, (-1, 0): 8}
    height, width = len(grid), len(grid[0])
    seen: dict[tuple[int, int], int] = {start: 0}
    queue: deque[tuple[int, int]] = deque([start])
    while queue:
        x, y = queue.popleft()
        if (x, y) == goal:
            return seen[(x, y)]
        for (step_x, step_y), bit in bits.items():
            reached = (x + step_x, y + step_y)
            if (grid[y][x] & bit == 0 and reached not in seen
                    and 0 <= reached[0] < width
                    and 0 <= reached[1] < height):
                seen[reached] = seen[(x, y)] + 1
                queue.append(reached)
    return -1
