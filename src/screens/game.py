from typing import Any, Optional

from manage_screen.renderer import InputEvent
from manage_screen.screen import Screen

from src import Direction, GameState, Maze, Level, Config
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
        self.player_image: str | None = None
        self.tick_accumulator: float = 0
        self.accumulator_ghost: float = 0
        self.pacgum_image: Any = None
        self.super_pacgum_image: Any = None
        self.lives: str | None = None

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
        self.tick_accumulator = 0
        self.accumulator_ghost = 0

        renderer: Any = kwargs.get("renderer")
        try:
            if renderer is not None:
                self.ghost_images = {
                    "blue": renderer.load_image
                    ("src/img/enemy_blue.png"),
                    "red": renderer.load_image("src/img/enemy_red.png"),
                    "orange": renderer.load_image("src/img/enemy_orange.png"),
                    "purple": renderer.load_image("src/img/enemy_purple.png"),
                }

            self.player_image = renderer.load_image("src/img/pac.png")
            self.pacgum_image = renderer.load_image("src/img/pacgum.png")
            self.super_pacgum_image = renderer.load_image("src/img/"
                                                          "super_pacgum.png")
            self.lives = renderer.load_image("src/img/life.png")
        except FileNotFoundError:
            print("Error file not found")
            sys.exit(1)

        if self.maze is None:
            renderer.draw_text("Maze unavailable", 20, 20, (255, 0, 0))
            return

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

        if GameState.level.state == Level.State.LOST:
            return "GAMEOVER"
        if GameState.level.state == Level.State.WON:
            return "MENU"  # TODO: change to WIN menu

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

    def update(self, dt: float) -> None:
        """Update the game unless it is paused.

        Args:
            dt: Time elapsed since the previous update, in milliseconds.
        """
        if self.paused:
            return

        GameState.level.update(int(dt))

        self.tick_accumulator += dt
        while (self.tick_accumulator >= Config.ms_per_tick):
            self.tick_accumulator = self.tick_accumulator % Config.ms_per_tick
            GameState.level.tick()

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
        """Draw the maze walls, centered in the renderer.

        Each cell draws a wall on every side where movement is blocked.

        Args:
            maze: The maze to draw.
            renderer: The renderer used to draw the walls.
        """
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

    def _draw_ghost(self, ghost: Any, index: int, renderer: Any,
                    cell_size: int, offset_x: int, offset_y: int) -> None:
        """Draw a ghost centered on its current maze cell.

        The ghost color is chosen from its index, cycling through the
        available ghost images.

        Args:
            ghost: The ghost to draw (must have a ``cell`` attribute).
            index: Index of the ghost, used to select its color.
            renderer: The renderer used to draw the image.
            cell_size: Size in pixels of one maze cell.
            offset_x: Horizontal offset in pixels of the maze.
            offset_y: Vertical offset in pixels of the maze.
        """
        colors: list[str] = list(self.ghost_images.keys())
        image = self.ghost_images[colors[index % len(colors)]]
        if image is None:
            return

        x = offset_x + ghost.cell.x * cell_size + cell_size // 2
        y = offset_y + ghost.cell.y * cell_size + cell_size // 2
        renderer.draw_image(image, x, y, cell_size, cell_size, centered=True)

    def _draw_player(self, player: Any, renderer: Any, cell_size: int,
                     offset_x: int, offset_y: int) -> None:
        """Draw the player centered on its position in the maze.

        Args:
            player: The player to draw (must have ``x`` and ``y`` attributes).
            renderer: The renderer used to draw the image.
            cell_size: Size in pixels of one maze cell.
            offset_x: Horizontal offset in pixels of the maze.
            offset_y: Vertical offset in pixels of the maze.
        """
        if (self.player_image is None):
            return
        x = offset_x + player.x * cell_size + cell_size // 2
        y = offset_y + player.y * cell_size + cell_size // 2
        renderer.draw_image(self.player_image, int(x), int(y), cell_size,
                            cell_size, centered=True)

    def _draw_pacgum(self, pacgum: Any, renderer: Any, cell_size: int,
                     offset_x: int, offset_y: int) -> None:
        """Draw a pacgum or super-pacgum centered on its maze cell.

        Args:
            pacgum: The pacgum to draw (must have a ``cell`` attribute).
            renderer: The renderer used to draw the image.
            cell_size: Size in pixels of one maze cell.
            offset_x: Horizontal offset in pixels of the maze.
            offset_y: Vertical offset in pixels of the maze.
        """
        is_super: bool = isinstance(pacgum, SuperPacGum)
        image = self.super_pacgum_image if is_super else self.pacgum_image
        if image is None:
            return

        x = offset_x + pacgum.cell.x * cell_size + cell_size // 2
        y = offset_y + pacgum.cell.y * cell_size + cell_size // 2
        if (image is None):
            return
        renderer.draw_image(image, int(x), int(y), cell_size, cell_size,
                            centered=True)

    def _draw_stat(self, renderer: Any) -> None:
        font_size: int = 45
        padding: int = (renderer.width * 0.5)
        cs = self._compute_cell_size(renderer)
        offset_x = ((renderer.width - self.maze.width * cs) // 2)
        offset_y = ((renderer.height - self.maze.height * cs) // 2) * 0.04
        renderer.draw_text(f"SCORE: {self.score}", (padding), offset_x,
                           font_size=font_size)
        renderer.draw_text(f"LEVEL: {self.score}",
                           ((renderer.width) + padding), offset_y,
                           font_size=font_size)
        original_width, original_height = self.lives.get_size()
        aspect_ratio = original_width / original_height
        life_width = int(renderer.width * 0.05)
        life_height = int(life_width / aspect_ratio)
        for i in range(GameState.lives):
            renderer.draw_image(self.lives,
                                offset_x + i * ((renderer.width * 0.04)),
                                offset_y, (life_width),
                                (life_height), centered=False)

    def draw(self, renderer: Any) -> None:
        """Draw the current maze or an error message if it is unavailable.

        Args:
            renderer: Renderer used to draw the game screen.
        """
        renderer.clear()
        self._draw_stat(renderer)
        if self.maze is None:
            renderer.draw_text("Maze unavailable", 20, 20, (255, 0, 0))
            return
        self._draw_maze(self.maze, renderer)
        cell_size = self._compute_cell_size(renderer)
        offset_x = (renderer.width - self.maze.width * cell_size) // 2
        offset_y = (renderer.height - self.maze.height * cell_size) // 2

        for pacgum in GameState.level.pacgums:
            self._draw_pacgum(pacgum, renderer, cell_size, offset_x, offset_y)

        for index, ghost in enumerate(GameState.level.ghosts):
            if ghost.shown:
                self._draw_ghost(ghost, index, renderer, cell_size, offset_x,
                                 offset_y)

        self._draw_player(GameState.level.player, renderer, cell_size,
                          offset_x, offset_y)
