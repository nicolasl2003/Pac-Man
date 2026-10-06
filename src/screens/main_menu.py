from typing import Optional, Any
import pygame
from manage_screen.screen import Screen
from manage_screen.button import Button
from manage_screen.sound import management_sound, quit_sound, SoundManager


class MainMenuScreen(Screen):
    """Display the main menu and handle navigation button input."""

    def __init__(self) -> None:
        """Initialize the menu buttons, logo, and sound effects."""
        self.buttons: list[Button] = [
            Button(220, 180, 200, 60, "START", action="GAME"),
            Button(220, 260, 200, 60, "HIGHSCORES", action="HIGHSCORES"),
            Button(220, 260, 200, 60, "INSTRUCTIONS", action="INSTRUCTIONS"),
            Button(220, 340, 200, 60, "QUIT", action="QUIT")
        ]
        self.logo: Optional[pygame.Surface] = None
        self.logo_path = "src/img/logo.png"
        management_sound(0, True)
        try:
            SoundManager.load("click", "src/sounds/select_sound.wav")
        except pygame.error as e:
            print(e)

    def on_enter(self, **kwargs: Any) -> None:
        """Size the logo and position the buttons relative to the window.

        Args:
            **kwargs: Activation context, optionally containing a renderer.
        """
        renderer: Any = kwargs.get("renderer")
        if (renderer is None):
            return

        screen_width = renderer.width
        screen_height = renderer.height

        if (self.logo is None):
            try:
                raw_logo = renderer.load_image(self.logo_path)
                original_width, original_height = raw_logo.get_size()
                aspect_ratio = original_width / original_height
                logo_width = int(screen_width * 0.7)
                logo_height = int(logo_width / aspect_ratio)
                self.logo = renderer.scale_image(raw_logo, logo_width,
                                                 logo_height)
            except FileNotFoundError as exc:
                print(f"[WARN] {exc}")

        bouton_width = int(screen_width * 0.37)
        button_height = int(screen_height * 0.09)
        spacing = int(screen_height * 0.04)

        label_actions = [
            ("START", "GAME"),
            ("HIGHSCORES", "HIGHSCORES"),
            ("INSTRUCTIONS", "INSTRUCTIONS"),
            ("QUIT", "QUIT"),
        ]

        total_height = len(label_actions) * button_height + (len(label_actions)
                                                             - 1) * spacing
        start_y = (screen_height - total_height) // 2 + 200

        self.buttons = []
        for i, (label, action) in enumerate(label_actions):
            x = (screen_width - bouton_width) // 2
            y = start_y + i * (button_height + spacing)
            self.buttons.append(Button(x, y, bouton_width, button_height,
                                       label, action=action))

    def handle_events(self, events: list[Any]) -> Optional[str]:
        """Handle quit requests, Escape, and button clicks.

        Args:
            events: User input events to process.

        Returns:
            The next screen name or ``QUIT``, or None if no transition occurs.
        """
        for event in events:
            if (event.kind == "QUIT"):
                quit_sound()
                return ("QUIT")
            if (event.kind == "KEY" and event.key == "ESCAPE"):
                return ("QUIT")

            for button in self.buttons:
                result = button.handle_event(event)
                if (result):
                    return (result)
        return (None)

    def update(self, dt: float) -> None:
        """Perform no state changes for the static main menu.

        Args:
            dt: Time elapsed since the previous update, in seconds.
        """
        return (None)

    def draw(self, renderer: Any) -> None:
        """Draw the background, logo, and menu buttons.

        Args:
            renderer: Renderer used to draw the menu.
        """
        renderer.clear((0, 0, 0))

        if (self.logo is None):
            try:
                self.logo = renderer.load_image(self.logo_path)
                self.logo = renderer.scale_image(self.logo, 300, 100)
            except FileNotFoundError as exc:
                print(f"[WARN] {exc}")

        if (self.logo is not None):
            center_x = renderer.width // 2
            renderer.center_image(self.logo, center_x,
                                  int(renderer.height * 0.14) + 20)

        for button in self.buttons:
            button.draw(renderer)
