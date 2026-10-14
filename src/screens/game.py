from typing import Any, Optional

from manage_screen.renderer import InputEvent
from manage_screen.screen import Screen

from src import Direction, GameState, Maze
from src import SuperPacGum
import sys


class Games(Screen):
    """Manage the active game and render its maze."""

    def __init__(self) -> None:
        """Initialize the state for a new game."""
        self.score: int = 0
        self.saved: bool = False
        self.maze: Optional[Maze] = None
        self.cell_size: int = 10
        self.maze_width_ratio: float = 0.8
        self.maze_height_ratio: float = 0.8
        self.paused: bool = False
        self.ghost_images: dict[str, Any] = {}
        self.player_image: str = None
        self.accumulator_player: float = 0
        self.accumulator_ghost: float = 0
        self.pacgum_image: Any = None
        self.super_pacgum_image: Any = None

    def on_enter(self, **kwargs: Any) -> None:
        """Get the current level's maze and reset the paused state.

        Args:
            **kwargs: Context passed when activating this screen.
        """
        try:
            self.maze = GameState.level.maze
        except Exception as error:
            print(f"Error: Maze generation failed: {error}")
        self.paused = False
        self.accumulator_player = 0
        self.accumulator_ghost = 0

        renderer: Any = kwargs.get("renderer")
        try:
            if renderer is not None:
                self.ghost_images = {
                    "blue": renderer.load_image("src/img/enemy_bleu-remove.png"),
                    "red": renderer.load_image("src/img/enemy_rouge.png"),
                    "yellow": renderer.load_image("src/img/enemy_jaune.png"),
                }

                self.player_image = renderer.load_image("src/img/pac-jaune2.png")
                self.pacgum_image = renderer.load_image("src/img/pacgum.png")
                self.super_pacgum_image = renderer.load_image("src/img/super_pacgum.png")
        except FileNotFoundError as e:
            print({e})
            sys.exit(1)

        if self.maze is None:
            renderer.draw_text("Maze unavailable", 20, 20, (255, 0, 0))
            return

        self._draw_maze(self.maze, renderer)
        cell_size = self._compute_cell_size(renderer)
        offset_x = (renderer.width - self.maze.width * cell_size) // 2
        offset_y = (renderer.height - self.maze.height * cell_size) // 2

        for pacgum in GameState.level.pacgums:
            self._draw_pacgum(pacgum, renderer, cell_size, offset_x, offset_y)

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        """Handle quit and pause requests.

        Args:
            events: User input events to process.

        Returns:
            ``QUIT`` or ``PAUSE`` when a transition is requested, else None.
        """
        KEY_TO_DIRECTION = {
            "UP": Direction.UP, "W": Direction.UP,
            "DOWN": Direction.DOWN, "S": Direction.DOWN,
            "LEFT": Direction.LEFT, "A": Direction.LEFT,
            "RIGHT": Direction.RIGHT, "D": Direction.RIGHT,
        }

        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")

            if (event.kind == "KEY" and event.key in ("ESCAPE", "PAUSE")):
                self.paused = True
                return ("PAUSE")
            if (event.kind == "KEY" and event.key in KEY_TO_DIRECTION):
                GameState.level.player.set_direction(KEY_TO_DIRECTION
                                                     [event.key])
        return (None)

    TICK_MS_PLAYER = 200
    TICK_MS_GHOST = 350

    def update(self, dt: float) -> None:
        """Update the game unless it is paused.

        Args:
            dt: Time elapsed since the previous update, in milliseconds.
        """
        if self.paused:
            return

        GameState.level.update(int(dt))

        self.accumulator_player += dt
        while (self.accumulator_player >= self.TICK_MS_PLAYER):
            self.accumulator_player -= self.TICK_MS_PLAYER
            GameState.level.player.tick()
        self.accumulator_ghost += dt
        while (self.accumulator_ghost >= self.TICK_MS_GHOST):
            self.accumulator_ghost -= self.TICK_MS_GHOST
            for ghost in GameState.level.ghosts:
                ghost.tick()

    def _compute_cell_size(self, renderer: Any) -> int:
        """Calculate a maze cell size that fits within the window.

        Args:
            renderer: Renderer providing the window dimensions.

        Returns:
            The cell size in pixels.

        Raises:
            ValueError: If the maze is missing or has invalid dimensions.
        """
        maze = self.maze
        if maze is None:
            raise ValueError("Error: missing maze")

        if maze.width <= 0 or maze.height <= 0:
            raise ValueError("Error: maze dimensions must be positive")

        available_width = renderer.width * self.maze_width_ratio
        available_height = renderer.height * self.maze_height_ratio
        cs_width = available_width / maze.width
        cs_height = available_height / maze.height

        return max(1, int(min(cs_width, cs_height)))

    def _draw_maze(self, maze: Maze, renderer: Any) -> None:
        cs = self._compute_cell_size(renderer)
        offset_x = (renderer.width - maze.width * cs) // 2
        offset_y = (renderer.height - maze.height * cs) // 2
        wall_color = (0, 0, 255)

        for cell in maze.cell_dict.values():
            px = offset_x + cell.x * cs
            py = offset_y + cell.y * cs
            right = px + cs
            bottom = py + cs

            if not cell.can_move(Direction.UP):
                renderer.draw_line((px, py), (right, py), wall_color)

            if not cell.can_move(Direction.LEFT):
                renderer.draw_line((px, py), (px, bottom), wall_color)

            if not cell.can_move(Direction.DOWN):
                renderer.draw_line((px, bottom), (right, bottom), wall_color)

            if not cell.can_move(Direction.RIGHT):
                renderer.draw_line((right, py), (right, bottom), wall_color)

    def _draw_ghost(self, ghost: Any, renderer: Any,
                    cell_size: int, offset_x: int, offset_y: int) -> None:
        """Draw a ghost centered on its current maze cell."""
        image = self.ghost_images.get("blue")
        if image is None:
            return

        x = offset_x + ghost.cell.x * cell_size + cell_size // 2
        y = offset_y + ghost.cell.y * cell_size + cell_size // 2
        renderer.draw_image(image, x, y, cell_size, cell_size, centered=True)

    def _draw_player(self, player: Any, renderer: Any, cell_size: int,
                     offset_x: int, offset_y: int) -> None:
        if (self.player_image is None):
            return
        x = offset_x + player.x * cell_size + cell_size // 2
        y = offset_y + player.y * cell_size + cell_size // 2
        renderer.draw_image(self.player_image, int(x), int(y), cell_size,
                            cell_size, centered=True)

    def _draw_pacgum(self, pacgum: Any, renderer: Any, cell_size: int,
                     offset_x: int, offset_y: int) -> None:
        is_super: bool = isinstance(pacgum, SuperPacGum)
        image = self.super_pacgum_image if is_super else self.pacgum_image
        if image is None:
            return

        x = offset_x + pacgum.cell.x * cell_size + cell_size // 2
        y = offset_y + pacgum.cell.y * cell_size + cell_size // 2
        if (image is None):
            return
        renderer.draw_image(image, int(x), int(y), cell_size, cell_size, centered=True)

    def draw(self, renderer: Any) -> None:
        """Draw the current maze or an error message if it is unavailable.

        Args:
            renderer: Renderer used to draw the game screen.
        """
        renderer.clear()
        if self.maze is None:
            renderer.draw_text("Maze unavailable", 20, 20, (255, 0, 0))
            return

        self._draw_maze(self.maze, renderer)
        cell_size = self._compute_cell_size(renderer)
        offset_x = (renderer.width - self.maze.width * cell_size) // 2
        offset_y = (renderer.height - self.maze.height * cell_size) // 2

        for pacgum in GameState.level.pacgums:
            self._draw_pacgum(pacgum, renderer, cell_size, offset_x, offset_y)

        for ghost in GameState.level.ghosts:
            self._draw_ghost(ghost, renderer, cell_size, offset_x, offset_y)

        self._draw_player(GameState.level.player, renderer, cell_size,
                          offset_x, offset_y)
