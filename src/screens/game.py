import sys
from collections import deque
from typing import Optional
from functools import lru_cache

import pygame

from manage_screen.renderer import InputEvent, PygameRenderer
from manage_screen.screen import Screen

from src import AssetError, Direction, GameState, Maze
from src import PacGum, SuperPacGum
from src import Ghost, Player, Rotation


class Games(Screen):
    """Manage the active game and render its maze."""

    _KONAMI = ("UP", "UP", "DOWN", "DOWN", "LEFT", "RIGHT", "LEFT",
               "RIGHT", "B", "A")
    _KEY_TO_DIRECTION = {
        "UP": Direction.UP, "W": Direction.UP, "Z": Direction.UP,
        "DOWN": Direction.DOWN, "S": Direction.DOWN,
        "LEFT": Direction.LEFT, "A": Direction.LEFT, "Q": Direction.LEFT,
        "RIGHT": Direction.RIGHT, "D": Direction.RIGHT,
    }

    def __init__(self) -> None:
        """Initialize the state for a new game."""
        self.score: int = 0
        self.saved: bool = False
        self.maze: Optional[Maze] = None
        self.cell_size: int = 10
        self.maze_width_ratio: float = 0.8
        self.maze_height_ratio: float = 0.8
        self.paused: bool = False
        self.last_keys: deque[str] = deque(maxlen=len(self._KONAMI))
        self.ghost_images: dict[str, pygame.Surface] = {}
        self.mirrored_images: dict[str, pygame.Surface] = {}
        self.player_image: dict[Rotation, pygame.Surface] = {}
        self.tick_accumulator: float = 0
        self.accumulator_ghost: float = 0
        self.pacgum_image: Optional[pygame.Surface] = None
        self.super_pacgum_image: Optional[pygame.Surface] = None
        self.player_previous: tuple[float, float] = (0.0, 0.0)
        self.ghosts_previous: list[tuple[float, float]] = []
        self.normal_lives: Optional[pygame.Surface] = None
        self.super_lives: Optional[pygame.Surface] = None

    @property
    def lives(self) -> Optional[pygame.Surface]:
        """Fetches the correct lives image depending on the cheat status."""

        return self.super_lives if GameState.cheat else self.normal_lives

    def on_enter(self, **kwargs: PygameRenderer) -> None:
        """Get the current level's maze and reset the paused state.

        Args:
            **kwargs: Context passed when activating this screen.
        """
        try:
            self.maze = GameState.level.maze
        except Exception as error:
            print(f"Error: Maze generation failed: {error}",
                  file=sys.stderr)
        self.paused = False
        self.tick_accumulator = 0
        self.accumulator_ghost = 0

        renderer: PygameRenderer = kwargs["renderer"]
        try:
            if renderer is not None:
                self.ghost_images = {
                    "blue": renderer.load_image("src/img/enemy_blue.png"),
                    "frightened_blue": renderer.load_image
                    ("src/img/enemy_frightened_blue.png"),
                    "red": renderer.load_image("src/img/enemy_red.png"),
                    "frightened_red": renderer.load_image
                    ("src/img/enemy_frightened_red.png"),
                    "orange": renderer.load_image("src/img/enemy_orange.png"),
                    "frightened_orange": renderer.load_image
                    ("src/img/enemy_frightened_orange.png"),
                    "purple": renderer.load_image("src/img/enemy_purple.png"),
                    "frightened_purple": renderer.load_image
                    ("src/img/enemy_frightened_purple.png"),
                }

            if (not self.mirrored_images):
                self.mirrored_images = {
                    color: renderer.mirror_image(image)
                    for color, image in self.ghost_images.items()
                }
            base = renderer.load_image("src/img/pac.png")
            self.player_image = {
                Rotation.RIGHT: base,
                Rotation.LEFT: renderer.mirror_image(base),
                Rotation.UP: renderer.rotate_image(base, 90),
                Rotation.DOWN: renderer.rotate_image(base, -90)
            }
            self.pacgum_image = renderer.load_image("src/img/pacgum.png")
            self.super_pacgum_image = renderer.load_image("src/img/"
                                                          "super_pacgum.png")
            self.normal_lives = renderer.load_image("src/img/life.png")
            self.super_lives = renderer.load_image("src/img/cheat_life.png")
        except OSError as error:
            raise AssetError("Sprites could not be loaded", error) from error

        if self.maze is None:
            renderer.draw_text("Maze unavailable", 20, 20, (255, 0, 0))
            return

        cell_size = self._compute_cell_size(renderer)
        offset_x = (renderer.width - self.maze.width * cell_size) // 2
        offset_y = (renderer.height - self.maze.height * cell_size) // 2

        for pacgum in GameState.level.pacgums:
            self._draw_pacgum(pacgum, renderer, cell_size, offset_x, offset_y)

        player = GameState.level.player
        self.player_previous = (float(player.x), float(player.y))
        self.ghosts_previous = [
            (float(ghost.cell.x), float(ghost.cell.y))
            for ghost in GameState.level.ghosts
        ]

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        """Handle quit and pause requests.

        Args:
            events: User input events to process.

        Returns:
            ``QUIT`` or ``PAUSE`` when a transition is requested, else None.
        """

        match GameState.level.state:
            case GameState.level.State.LOST:
                return ("END")
            case GameState.level.State.WON:
                if (not GameState.next_stage()):
                    return ("END")
                self.maze = GameState.level.maze
            case GameState.level.State.TIMEDOUT:
                return ("TIMEOUT")

        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")
            if (event.kind != "KEY" or event.key is None):
                continue

            self.last_keys.append(event.key)
            if (tuple(self.last_keys) == self._KONAMI):
                GameState.cheat = not GameState.cheat
                self.last_keys.clear()

            if (event.key in ("ESCAPE", "P")):
                self.paused = True
                return ("PAUSE")
            if (event.key == "N" and GameState.cheat):
                GameState.level.state = GameState.level.State.WON
            try:
                GameState.level.player.set_direction(
                    self._KEY_TO_DIRECTION[event.key])
            except KeyError:
                pass
        return (None)

    def update(self, dt: float) -> None:
        """Update the game unless it is paused.

        Args:
            dt: Time elapsed since the previous update, in milliseconds.
        """
        if self.paused:
            return

        self.tick_accumulator += dt
        while (self.tick_accumulator >= GameState.tick_ms):
            player = GameState.level.player
            self.player_previous = (float(player.x), float(player.y))

            self.ghosts_previous = [
                (float(ghost.cell.x), float(ghost.cell.y))
                for ghost in GameState.level.ghosts
            ]
            GameState.level.tick()
            self.tick_accumulator = self.tick_accumulator % GameState.tick_ms

    def _compute_cell_size(self, renderer: PygameRenderer) -> int:
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

    def _draw_maze(self, maze: Maze, renderer: PygameRenderer) -> None:
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

    def _draw_ghost(self, ghost: Ghost, index: int, renderer: PygameRenderer,
                    cell_size: int, offset_x: int, offset_y: int,
                    previous: tuple[float, float]) -> None:
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
        color: str = colors[(index * 2) % len(colors)]
        if ghost.mode is Ghost.GhostMode.EDIBLE:
            color = f"frightened_{color}"
        image = (self.mirrored_images[color]
                 if ghost.rotation is Rotation.LEFT
                 else self.ghost_images[color])
        if image is None:
            return

        current = (float(ghost.cell.x), float(ghost.cell.y))
        grid_x, grid_y = self._interpolate_position(previous, current)

        x = offset_x + grid_x * cell_size + cell_size // 2
        y = offset_y + grid_y * cell_size + cell_size // 2
        renderer.draw_image(image, int(x), int(y), cell_size, cell_size,
                            centered=True)

    def _interpolate_position(
        self,
        previous: tuple[float, float],
        current: tuple[float, float],
        factor: float = 1.0,
            ) -> tuple[float, float]:
        """Interpolate a grid position between two game ticks."""
        duration = GameState.tick_ms
        if duration <= 0:
            return current

        alpha = min(1.0, self.tick_accumulator / duration)
        alpha *= factor

        x = previous[0] + (current[0] - previous[0]) * alpha
        y = previous[1] + (current[1] - previous[1]) * alpha
        return x, y

    def _draw_player(self, player: Player, renderer: PygameRenderer,
                     cell_size: int, offset_x: int, offset_y: int) -> None:
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

        current = (float(player.x), float(player.y))
        grid_x, grid_y = self._interpolate_position(
            self.player_previous,
            current,
            factor=0.7,
        )

        image = self.player_image.get(player.rotation)
        if (image is None):
            return
        x = offset_x + grid_x * cell_size + cell_size / 2
        y = offset_y + grid_y * cell_size + cell_size / 2
        renderer.draw_image(image, int(x), int(y), cell_size,
                            cell_size, centered=True)

    def _draw_pacgum(self, pacgum: PacGum | SuperPacGum,
                     renderer: PygameRenderer, cell_size: int,
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

    def _draw_stat(self, renderer: PygameRenderer) -> None:
        """Draw the lives, score, level and time left above the maze.

        Args:
            renderer: Renderer used to draw the HUD.
        """
        if self.maze is None or self.lives is None:
            return
        cs = self._compute_cell_size(renderer)
        maze_width = self.maze.width * cs
        offset_x = (renderer.width - maze_width) // 2
        offset_y = (renderer.height - self.maze.height * cs) // 2
        font_size = self._compute_stat_font_size(renderer, offset_y,
                                                 maze_width)
        score_template, _, time_template, max_lives = self._stat_bounds()
        score_width, text_height = renderer.get_text_size(score_template,
                                                          font_size)
        text_y = (offset_y - text_height) // 2
        gap = text_height

        original_width, original_height = self.lives.get_size()
        life_width = text_height * original_width // original_height
        for i in range(GameState.lives):
            renderer.draw_image(self.lives,
                                offset_x + i * (life_width + gap // 4),
                                text_y, life_width, text_height,
                                centered=False)
        score_x = offset_x + max_lives * (life_width + gap // 4) + gap
        renderer.draw_text(f"SCORE: {GameState.score}", score_x, text_y,
                           font_size=font_size)
        renderer.draw_text(f"LEVEL: {GameState.stage}",
                           score_x + score_width + gap, text_y,
                           font_size=font_size)
        time_width = renderer.get_text_size(time_template, font_size)[0]
        renderer.draw_text(f"TIME: {GameState.timer_s}",
                           offset_x + maze_width - time_width, text_y,
                           font_size=font_size)

    def _stat_bounds(self) -> tuple[str, str, str, int]:
        """Return what the HUD is laid out for, so it never moves.

        Returns:
            The score, level and time texts at their widest, digits
            replaced by zeros, then the most lives the player can have.
        """
        from src import Config

        score_digits = max(6, len(str(GameState.score)))
        time_digits = len(str(Config.level_time))
        return (f"SCORE: {'0' * score_digits}", "LEVEL: 00",
                f"TIME: {'0' * time_digits}", Config.lives)

    @lru_cache
    def _compute_stat_font_size(self, renderer: PygameRenderer, margin: int,
                                width: int) -> int:
        """Find the largest font size that fits the HUD above the maze.

        Args:
            renderer: Renderer used to measure the texts.
            margin: Height in pixels of the space above the maze.
            width: Width in pixels of the maze.

        Returns:
            Font size in points.
        """
        if (self.lives is None):
            return (8)
        original_width, original_height = self.lives.get_size()
        score, level, time_left, max_lives = self._stat_bounds()
        font_size = max(8, min(45, margin // 2))
        while (font_size > 8):
            score_width, gap = renderer.get_text_size(score, font_size)
            life_width = gap * original_width // original_height
            lives_width = max_lives * (life_width + gap // 4)
            level_width = renderer.get_text_size(level, font_size)[0]
            time_width = renderer.get_text_size(time_left, font_size)[0]
            if (lives_width + score_width + level_width + time_width
                    + 3 * gap <= width):
                break
            font_size -= 1
        return (font_size)

    def draw(self, renderer: PygameRenderer) -> None:
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
                previous = self.ghosts_previous[index]
                self._draw_ghost(ghost, index, renderer, cell_size, offset_x,
                                 offset_y, previous)

        self._draw_player(GameState.level.player, renderer, cell_size,
                          offset_x, offset_y)
