from typing import Any
from . import Config
from mazegenerator import MazeGenerator

WALL_NORTH = 1
WALL_EAST = 2
WALL_SOUTH = 4
WALL_WEST = 8


class MazeGenerate:
    """Wrapper around the external MazeGenerator package."""

    def __init__(self, width: int, height: int) -> None:
        self._generator: MazeGenerator = MazeGenerator(
            size=(width, height),
            entry_cell=(width, height),
            perfect=False,
            seed=Config.seed,
        )
        self.grid: list[list[int]] = self._generator.maze
        self.height: int = len(self.grid)
        self.width: int = len(self.grid[0])
        self.entry = self._generator.maze_entry
        self.exit = self._generator.maze_exit

    def has_wall_north(self, x: int, y: int) -> bool:
        """Return True if there is a wall above cell (x, y)."""
        return (bool(self.grid[y][x] & WALL_NORTH))

    def has_wall_east(self, x: int, y: int) -> bool:
        """Return True if there is a wall to the right of cell (x, y)."""
        return (bool(self.grid[y][x] & WALL_EAST))

    def has_wall_south(self, x: int, y: int) -> bool:
        """Return True if there is a wall below cell (x, y)."""
        return (bool(self.grid[y][x] & WALL_SOUTH))

    def has_wall_west(self, x: int, y: int) -> bool:
        """Return True if there is a wall to the left of cell (x, y)."""
        return (bool(self.grid[y][x] & WALL_WEST))


def generate_maze(width: int = 10, height: int = 10) -> MazeGenerate:
    """Create and return a new MazeGenerate instance.

    width -- number of columns
    height -- number of rows
    """
    try:
        return (MazeGenerate(width=width, height=height))
    except Exception as e:
        raise RuntimeError(f"Maze generation failed: {e}")
