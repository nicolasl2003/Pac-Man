from . import config
from typing import Any
import sys

try:
    from mazegenerator import MazeGenerator
except Exception:
    print("[ERRROR] missing package {mazegenetor}")
    sys.exit(1)

WALL_NORTH = 1
WALL_EAST = 2
WALL_SOUTH = 4
WALL_WEST = 8


class MazeRender:
    """Adapt the external maze generator to the game's maze interface."""

    def __init__(self, width: int, height: int) -> None:
        """Generate a maze and store its grid and dimensions.

        Args:
            width: Requested number of columns.
            height: Requested number of rows.
        """
        self._generator: Any = MazeGenerator(
            size=(width, height),
            entry_cell=(width, height),
            perfect=False,
            seed=config.Config.seed,
        )
        self.grid: list[list[int]] = self._generator.maze
        self.height: int = len(self.grid)
        self.width: int = len(self.grid[0])
        self.entry = self._generator.maze_entry
        self.exit = self._generator.maze_exit

    def has_wall_north(self, x: int, y: int) -> bool:
        """Check whether a cell has a wall on its north side.

        Args:
            x: Column index of the cell.
            y: Row index of the cell.

        Returns:
            True if the cell has a north wall.
        """
        return (bool(self.grid[y][x] & WALL_NORTH))

    def has_wall_east(self, x: int, y: int) -> bool:
        """Check whether a cell has a wall on its east side.

        Args:
            x: Column index of the cell.
            y: Row index of the cell.

        Returns:
            True if the cell has an east wall.
        """
        return (bool(self.grid[y][x] & WALL_EAST))

    def has_wall_south(self, x: int, y: int) -> bool:
        """Check whether a cell has a wall on its south side.

        Args:
            x: Column index of the cell.
            y: Row index of the cell.

        Returns:
            True if the cell has a south wall.
        """
        return (bool(self.grid[y][x] & WALL_SOUTH))

    def has_wall_west(self, x: int, y: int) -> bool:
        """Check whether a cell has a wall on its west side.

        Args:
            x: Column index of the cell.
            y: Row index of the cell.

        Returns:
            True if the cell has a west wall.
        """
        return (bool(self.grid[y][x] & WALL_WEST))


def generate_maze(width: int = 10, height: int = 10) -> MazeRender:
    """Generate a maze and return its adapter instance.

    Args:
        width: Requested number of columns.
        height: Requested number of rows.

    Returns:
        An adapter containing the generated grid and wall queries.

    Raises:
        RuntimeError: If maze generation fails.
    """
    try:
        return (MazeRender(width=width, height=height))
    except Exception as e:
        raise RuntimeError(f"Maze generation failed: {e}")
