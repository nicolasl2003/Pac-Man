from typing import Optional, Any
from manage_screen.screen import Screen
from manage_screen.button import Button
from ..scores import save_score


class GameOverScreen(Screen):
    """Display the final score and post-game options."""

    def __init__(self) -> None:
        """Initialize the final score and game-over buttons."""
        self.score: int = 0
        self.saved: bool = False

        self.retry_button = Button(220, 290, 200, 50, "REPLAY", action="GAME")
        self.menu_button = Button(220, 290, 200, 50, "MENU", action="MENU")

    def on_enter(self, **kwargs: Any) -> None:
        """Store and save the score supplied when entering this screen.

        Args:
            **kwargs: Activation context, optionally containing the final
                score.
        """
        self.score = kwargs.get("score", 0)
        self.saved = False

        save_score("PLAYER", self.score)
        self.saved = True

    def handle_events(self, events: list[Any]) -> Optional[Any]:
        """Handle the return-to-menu request and retry button clicks.

        Args:
            events: User input events to process.

        Returns:
            The next screen identifier, or None if no transition occurs.
        """
        for event in events:
            if (getattr(event, "key", None) == "ESCAPE"):
                return ("MENU")
            result = self.retry_button.handle_event(event)
            if (result):
                return (result)
        return None

    def update(self, dt: float) -> None:
        """Perform no state changes for the game-over screen.

        Args:
            dt: Time elapsed since the previous update, in seconds.
        """
        pass

    def draw(self, renderer: Any) -> None:
        """Draw the game-over message, final score, and available buttons.

        Args:
            renderer: Renderer used to draw the screen.
        """
        renderer.clear((0, 0, 0))
        renderer.draw_text("GAME OVER", 200, 60, (255, 0, 0), big=True)
        renderer.draw_text(
            f"score: {self.score}", 210, 140, (255, 255, 255)
        )

        self.retry_button.draw(renderer)
        self.menu_button.draw(renderer)
