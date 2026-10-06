from typing import Any, Optional

from manage_screen.renderer import InputEvent
from manage_screen.screen import Screen

from src import GameState

from ..maze_render import MazeRender, generate_maze


class Games(Screen):
    """Manage the active game and render its maze."""

    def __init__(self) -> None:
        """Initialize the state for a new game."""
        self.score: int = 0
        self.saved: bool = False
        self.maze: Optional[Any] = None
        self.cell_size: int = 10
        self.maze_width_ratio: float = 0.8
        self.maze_height_ratio: float = 0.8
        self.paused: bool = False

    def on_enter(self, **kwargs: Any) -> None:
        """Generate a maze and reset the paused state.

        Args:
            **kwargs: Context passed when activating this screen.
        """
        try:
            GameState
            self.maze = generate_maze(width=30, height=30)
        except RuntimeError as e:
            print(f"[ERROR] {e}")
        self.paused = False

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        """Handle quit and pause requests.

        Args:
            events: User input events to process.

        Returns:
            ``QUIT`` or ``PAUSE`` when a transition is requested, else None.
        """
        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")

            if (event.kind == "KEY" and event.key in ("ESCAPE", "PAUSE")):
                self.paused = True
                return ("PAUSE")
        return (None)

    def update(self, dt: float) -> None:
        """Update the game unless it is paused.

        Args:
            dt: Time elapsed since the previous update, in seconds.
        """
        if (self.paused):
            return

    def _compute_cell_size(self, renderer: Any) -> int:
        """Calculate a maze cell size that fits within the window.

        Args:
            renderer: Renderer providing the window dimensions.

        Returns:
            The maximum cell size in pixels.

            Raises:
                ZeroDivisionError on null maze height or maze width
                ... if maze is null
        """
        maze = self.maze
        if maze is None:
            raise ValueError("Error: missing maze")

        available_width = renderer.width / self.maze_width_ratio
        available_height = renderer.height * self.maze_height_ratio
        cs_width = available_width / maze.width
        cs_height = available_height / maze.height
        if maze.width == 0 or maze.height == 0:
            raise ValueError("Error: missing width in maze")

        return int(min(cs_width, cs_height))

    def _draw_maze(self, maze: MazeRender, renderer: Any) -> None:
        cs = self._compute_cell_size(renderer)
        offset_x = (renderer.width - maze.width * cs) // 2
        offset_y = (renderer.height - maze.height * cs) // 2
        wall_color = (0, 0, 255)

        for y in range(maze.height):
            for x in range(maze.width):
                px = offset_x + x * cs
                py = offset_y + y * cs

                if maze.has_wall_north(x, y):
                    renderer.draw_line((px, py), (px + cs, py),
                                       wall_color)

                if maze.has_wall_west(x, y):
                    renderer.draw_line((px, py), (px, py + cs),
                                       wall_color)

                if maze.has_wall_south(x, y):
                    renderer.draw_line((px, py + cs), (px + cs, py + cs),
                                       wall_color)

                if maze.has_wall_east(x, y):
                    renderer.draw_line((px + cs, py), (px + cs, py + cs),
                                       wall_color)

    def draw(self, renderer: Any) -> None:
        """Draw the maze or an error message if generation failed.

        Args:
            renderer: Renderer used to draw the game screen.
        """
        renderer.clear((0, 0, 0))
        if (self.maze is None):
            renderer.draw_text("Maze generation failed", 20, 20, (255, 0, 0))
            return
        self._draw_maze(self.maze, renderer)
