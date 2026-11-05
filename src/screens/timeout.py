from typing import Optional, Any
from manage_screen.screen import Screen
from manage_screen.button import Button
from manage_screen.renderer import PygameRenderer, Color
from src import GameState


class TimeoutScreen(Screen):
    """Display options for resuming the game or returning to the menu."""

    def __init__(self) -> None:
        """Initialize the pause screen title and buttons."""
        self.retry_button: Optional[Button] = None
        self.menu_button: Optional[Button] = None

    def on_enter(self, **kwargs: Any) -> None:
        """Perform setup when the pause screen becomes active.

        Args:
            **kwargs: Context passed when activating this screen.
        """
        pass

    def _ensure_buttons(self, renderer: Any) -> None:
        """Create or reposition the buttons based on the window dimensions.

        Args:
            renderer: Renderer providing the window dimensions.
        """
        width = renderer.width
        height = renderer.height
        btn_w, btn_h = 280, 60
        spacing = int(height * 0.01)

        x = (width - btn_w) // 2
        resume_y = int(height * 0.45)
        menu_y = resume_y + btn_h + spacing

        if (self.retry_button is None):
            self.retry_button = Button(x, resume_y, btn_w, btn_h, "RETRY",
                                       action="GAME")
        else:
            self.retry_button.x = x
            self.retry_button.y = resume_y

        if (self.menu_button is None):
            self.menu_button = Button(x, menu_y, btn_w, btn_h, "GIVE UP",
                                      action="END")
        else:
            self.menu_button.x = x
            self.menu_button.y = menu_y

    def handle_events(self, events: list[Any]) -> Optional[Any]:
        """Handle resume, menu navigation, and quit input.

        Args:
            events: User input events to process.

        Returns:
            The next screen identifier, or None if no transition occurs.
        """
        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")
            if (event.kind == "KEY" and event.key in ("ESCAPE", "P")):
                return ("GAME")

            if (self.retry_button):
                result = self.retry_button.handle_event(event)
                if (result):
                    GameState.retry_stage()
                    return (result)

            if (self.menu_button):
                result = self.menu_button.handle_event(event)
                if (result):
                    GameState.give_up()
                    return (result)
        return None

    def update(self, dt: float) -> None:
        """Perform no state changes while the pause screen is displayed.

        Args:
            dt: Time elapsed since the previous update, in seconds.
        """
        pass

    def _draw_centered(self, renderer: PygameRenderer, text: str, y: int,
                       color: Color, font_size: int) -> None:
        """Draws one line of text centered on the window.

        renderer -- The renderer to draw with
        text -- The line to draw
        y -- The distance from the top of the window
        color -- The color of the line
        font_size -- The height of the font to use
        """

        width: int = renderer.get_text_size(text, font_size)[0]
        renderer.draw_text(text, (renderer.width - width) // 2, y,
                           color, font_size)

    def draw(self, renderer: Any) -> None:
        """Draw the pause screen as an overlay.

        Args:
            renderer: The renderer used to draw on screen.
        """

        self._draw_centered(renderer, "TIMEOUT", y=270, color=(255, 0, 0),
                            font_size=78)
        self._ensure_buttons(renderer)

        if self.retry_button:
            self.retry_button.draw(renderer)
        if self.menu_button:
            self.menu_button.draw(renderer)
