from typing import Optional, Any
from manage_screen.screen import Screen
from manage_screen.button import Button


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

    def on_enter(self, **kwargs: Any) -> None:
        """Perform any setup required when entering the screen.

        Args:
            **kwargs: Context passed when activating this screen.
        """
        pass

    def handle_events(self, events: list[Any]) -> Optional[str]:
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
                if event.pos:
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

    def _ensure_button(self, renderer: Any) -> None:
        """Create or reposition the back button relative to the window size.

        Args:
            renderer: Renderer providing the window dimensions.
        """
        width = renderer.width
        height = renderer.height
        btn_w, btn_h = 250, 50
        x = (width - btn_w) // 2
        y = height - btn_h - int(height * 0.15)

        if self.back_button is None:
            self.back_button = Button(x, y, btn_w, btn_h,
                                      "BACK", action="MENU")
        else:
            self.back_button.x = x
            self.back_button.y = y

    def draw(self, renderer: Any) -> None:
        """Draw the instructions screen.

        Args:
            renderer: The renderer used to draw on screen.
        """
        self._ensure_button(renderer)
        renderer.clear()

        width = renderer.width
        height = renderer.height

        title_font_size = max(16, int(height * 0.045))
        text_font_size = max(12, int(height * 0.025))
        line_height = int(height * 0.05)
        start_y = int(height * 0.12)

        for i, line in enumerate(self.lines):
            if not line:
                continue
            is_title = (i == 0)
            color = (255, 255, 0) if is_title else (255, 255, 255)
            font_size = title_font_size if is_title else text_font_size

            text_width, _ = renderer.get_text_size(line, font_size)
            x = (width - text_width) // 2
            y = start_y + i * line_height

            renderer.draw_text(line, x, y, color=color, font_size=font_size)

        if self.back_button:
            self.back_button.draw(renderer)
