from typing import Optional, Any
from manage_screen.screen import Screen
from manage_screen.button import Button
import pygame
from ..scores import load_scores, Score


class HighscoresScreen(Screen):
    """Display the high scores and a button to return to the menu."""

    def __init__(self) -> None:
        """Initialize the score list and navigation buttons."""
        self.buttons: list[Button] = []
        self.scores: list[Score] = []

    def on_enter(self, **kwargs: Any) -> None:
        """Load scores and prepare the navigation button.

        Args:
            **kwargs: Activation context, optionally containing a renderer.
        """
        renderer: Any = kwargs.get("renderer")
        if (renderer is None):
            return
        self.title_font = pygame.font.SysFont(None, 60)
        self.score_font = pygame.font.SysFont(None, 36)
        self.scores = load_scores()

        self.buttons = [
            self.create_button_ratio(renderer, "BACK", "MENU",
                                     width_ratio=0.37, height_ratio=0.09,
                                     x_ratio=0.5, y_ratio=0.80)
        ]

    def create_button_ratio(self, renderer: Any, text: str,
                            action: str, height_ratio: float,
                            width_ratio: float, x_ratio: float,
                            y_ratio: float) -> Button:
        """Create a button positioned and sized relative to the window.

        Args:
            renderer: Renderer providing the window dimensions.
            text: Label displayed on the button.
            action: Identifier of the action triggered by a click.
            height_ratio: Fraction of the window height used for button height.
            width_ratio: Fraction of the window width used for button width.
            x_ratio: Horizontal center position as a fraction of window width.
            y_ratio: Vertical center position as a fraction of window height.

        Returns:
            A button sized and positioned using the supplied ratios.
        """
        screen_width = renderer.width
        screen_height = renderer.height

        width = int(screen_width * width_ratio)
        height = int(screen_height * height_ratio)
        x = int(screen_width * x_ratio) - width // 2
        y = int(screen_height * y_ratio) - height // 2

        return (Button(x=x, y=y, width=width, height=height,
                       text=text, action=action))

    def handle_events(self, events: list[Any]) -> Optional[str]:
        """Handle quit requests and clicks on navigation buttons.

        Args:
            events: User input events to process.

        Returns:
            The next screen name or ``QUIT``, or None if no transition occurs.
        """
        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")
            if (event.kind == "KEY" and event.key == "ESCAPE"):
                return ("MENU")

            for button in self.buttons:
                result = button.handle_event(event)
                if (result):
                    return (result)
        return (None)

    def update(self, dt: float) -> None:
        """Perform no state changes for the high-score screen.

        Args:
            dt: Time elapsed since the previous update, in seconds.
        """
        pass

    def draw(self, renderer: Any) -> None:
        """Draw the title, available scores, and return button.

        Args:
            renderer: Renderer used to draw the screen.
        """
        renderer.clear()
        screen_width = renderer.width
        title_surface = self.title_font.render("HIGHSCORES",
                                               True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(screen_width // 2, 60))
        renderer.screen.blit(title_surface, title_rect)

        if (not self.scores):
            no_score_surface = self.score_font.render(
                "No score recorded", True, (255, 255, 255)
            )
            no_score_rect = no_score_surface.get_rect(
                center=(screen_width // 2, 150)
            )
            renderer.screen.blit(no_score_surface, no_score_rect)
        else:
            start_y = 160
            line_spacing = 50

            for index, score_entry in enumerate(self.scores):
                name, score = score_entry["name"], score_entry["score"]
                text = f"{index + 1}. {name} - {score}"
                score_surface = self.score_font.render(text,
                                                       True, (255, 255, 255))
                score_rect = score_surface.get_rect(center=(
                    screen_width // 2, start_y + index * line_spacing))
                renderer.screen.blit(score_surface, score_rect)

        for button in self.buttons:
            button.draw(renderer)
