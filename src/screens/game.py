from typing import Optional
from manage_screen.screen import Screen
from manage_screen.renderer import PygameRenderer, InputEvent
from typing import Optional
from ..maze_generate import MazeGenerator, generate_maze
from manage_screen.button import Button
from ..scores import save_score


class Games(Screen):
    def __init__(self) -> None:
        self.score: int = 0
        self.saved: bool = False
        self.maze: Optional[MazeGenerator] = None
        self.cell_size: int = 10
        self.maze_width_ratio: float = 0.8
        self.maze_height_ratio: float = 0.8

    def on_enter(self, **kwargs) -> None:
        try:
            self.maze = generate_maze(width=30, height=30)
        except RuntimeError as e:
            print(f"[ERROR] {e}")

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")
        return (None)

    def update(self, dt: float) -> None:
        pass

    def _compute_cell_size(self, renderer: PygameRenderer) -> int:
        available_width = renderer.width / self.maze_width_ratio
        available_height = renderer.height * self.maze_height_ratio

        cs_width = available_width / self.maze.width
        cs_height = available_height / self.maze.height

        return (min(cs_width, cs_height))

    def draw(self, renderer: PygameRenderer) -> None:
        renderer.clear((0, 0, 0))
        if (self.maze is None):
            renderer.draw_text("Maze generation failed", 20, 20, (255, 0, 0))
            return

        cs = self._compute_cell_size(renderer)
        offset_x = (renderer.width - self.maze.width * cs) // 2
        offset_y = (renderer.height - self.maze.height * cs) // 2
        wall_color = (0, 0, 255)

        for y in range(self.maze.height):
            for x in range(self.maze.width):
                px = offset_x + x * cs
                py = offset_y + y * cs

                if self.maze.has_wall_north(x, y):
                    renderer.draw_line((px, py), (px + cs, py),
                                       wall_color, 2)

                if self.maze.has_wall_west(x, y):
                    renderer.draw_line((px, py), (px, py + cs),
                                       wall_color, 2)

                if self.maze.has_wall_south(x, y):
                    renderer.draw_line((px, py + cs), (px + cs, py + cs),
                                       wall_color, 2)

                if self.maze.has_wall_east(x, y):
                    renderer.draw_line((px + cs, py), (px + cs, py + cs),
                                       wall_color, 2)
