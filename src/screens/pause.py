from typing import Optional, Any
from manage_screen.screen import Screen
from manage_screen.button import Button


class PauseScreen(Screen):
    """Display options for resuming the game or returning to the menu."""

    def __init__(self) -> None:
        """Initialize the pause screen title and buttons."""
        self.resume_button: Optional[Button] = None
        self.menu_button: Optional[Button] = None
        self.title_path = "src/img/pause.png"
        self.snapshot = None

    def on_enter(self, **kwargs: Any) -> None:
        """Perform setup when the pause screen becomes active.

        Args:
            **kwargs: Context passed when activating this screen.
        """
        renderer: Any = kwargs.get("renderer")

        width = renderer.width
        height = renderer.height
        try:
            image = renderer.load_image(self.title_path)
            original_width, original_height = image.get_size()
            aspect_ratio = original_width / original_height
            logo_width = int(width * 0.3)
            logo_height = int(logo_width / aspect_ratio)
            renderer.draw_image(image, int(width // 2), (height * 0.3), logo_width, logo_height, centered=True)
        except FileNotFoundError:
            print("File not found")

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

        if (self.resume_button is None):
            self.resume_button = Button(x, resume_y, btn_w, btn_h, "RESUME",
                                        action="RESUME")
        else:
            self.resume_button.x = x
            self.resume_button.y = resume_y

        if (self.menu_button is None):
            self.menu_button = Button(x, menu_y, btn_w, btn_h, "MAIN MENU",
                                      action="MENU")
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
            if (event.kind == "KEY" and event.key in ("ESCAPE", "PAUSE")):
                return ("GAME")

            if (self.resume_button):
                result = self.resume_button.handle_event(event)
                if (result):
                    return (result)

            if (self.menu_button):
                result = self.menu_button.handle_event(event)
                if (result):
                    return (result)
        return None

    def update(self, dt: float) -> None:
        """Perform no state changes while the pause screen is displayed.

        Args:
            dt: Time elapsed since the previous update, in seconds.
        """
        pass

    def draw(self, renderer: Any) -> None:
        """Draw the pause screen as an overlay.

        Args:
            renderer: The renderer used to draw on screen.
        """
        self._ensure_buttons(renderer)

        if self.resume_button:
            self.resume_button.draw(renderer)
        if self.menu_button:
            self.menu_button.draw(renderer)
