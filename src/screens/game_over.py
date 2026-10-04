from typing import Optional, Any
from manage_screen.screen import Screen
from manage_screen.button import Button
from ..scores import save_score


class GameOverScreen(Screen):
    def __init__(self) -> None:
        self.score: int = 0
        self.saved: bool = False

        self.retry_button = Button(220, 290, 200, 50, "REJOUER", action="GAME")
        self.menu_button = Button(220, 290, 200, 50, "MENU", action="MENU")

    def on_enter(self, **kwargs: Any) -> None:
        self.score = kwargs.get("score", 0)
        self.saved = False

        save_score("PLAYER", self.score)
        self.saved = True

    def handle_events(self, events: list[Any]) -> Optional[Any]:
        for event in events:
            if (getattr(event, "key", None) == "ESCAPE"):
                return ("MENU")
            result = self.retry_button.handle_event(event)
            if (result):
                return (result)
        return None

    def update(self, dt: float) -> None:
        pass

    def draw(self, renderer: Any) -> None:
        renderer.clear((0, 0, 0))
        renderer.draw_text("GAME OVER", 200, 60, (255, 0, 0), big=True)
        renderer.draw_text(
            f"score final: {self.score}", 210, 140, (255, 255, 255)
        )

        self.retry_button.draw(renderer)
        self.menu_button.draw(renderer)
