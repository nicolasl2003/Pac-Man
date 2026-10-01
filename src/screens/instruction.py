from typing import Optional
from ..screen import Screen
from ..renderer import PygameRenderer, InputEvent
from ..button import Button


class InstructionsScreen(Screen):
    """Screen displaying game rules and controls."""

    def __init__(self) -> None:
        """Initialize the instructions screen."""
        self.back_button: Button = Button(220, 400, 250, 50,
                                          "BACK", action="MENU")
        self.lines: list[str] = [
            "HOW TO PLAY",
            "",
            "Move: ARROW KEYS / WASD",
            "Eat all the pacgums to win",
            "Avoid the ghosts or lose a life",
            "Super pacgums make ghosts vulnerable",
            "Eat vulnerable ghosts for bonus points",
        ]

    def on_enter(self, **kwargs) -> None:
        """Called when entering this screen."""
        pass

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        """Handle input events for this screen.

        Args:
            events: List of input events to process.

        Returns:
            The name of the next screen to switch to, or None to stay.
        """
        for event in events:
            if event.kind == "QUIT":
                return "QUIT"
            if event.kind == "KEY" and event.key == "ESCAPE":
                return "MENU"

            if event.kind == "MOTION":
                self.back_button.update_hover(event.pos[0], event.pos[1])

            if event.kind == "CLICK":
                if self.back_button.handle_event(event):
                    return self.back_button.action

        return None

    def update(self, dt: float) -> None:
        """Update screen state.

        Args:
            dt: Delta time in seconds since last frame.
        """
        pass

    def draw(self, renderer: PygameRenderer) -> None:
        """Draw the instructions screen.

        Args:
            renderer: The renderer used to draw on screen.
        """
        renderer.clear((0, 0, 0))

        start_y = 80
        line_height = 40

        for i, line in enumerate(self.lines):
            if not line:
                continue
            is_title = (i == 0)
            color = (255, 255, 0) if is_title else (255, 255, 255)
            font_size = 36 if is_title else 24

            text_width, _ = renderer.get_text_size(line, font_size)
            x = (renderer.width - text_width) // 2
            y = start_y + i * line_height

            renderer.draw_text(line, x, y, color=color, font_size=font_size)

        self.back_button.draw(renderer)
