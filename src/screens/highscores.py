from typing import Optional
from ..screen import Screen, InputEvent
from ..renderer import PygameRenderer
from ..button import Button
from ..scores import load_scores


class HighscoresScreen(Screen):
    def __init__(self) -> None:
        self.back_button: Button = Button(220, 400, 200, 50,
                                          "BACK", action="MENU")
        self.scores: list[tuple] = []

    def on_enter(self, **kwargs) -> None:
        self.scores = load_scores()

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")
            if (event.kind == "KEY" and event.key == "ESCAPE"):
                return ("QUIT")

            result = self.back_button.handle_event(event)
            if (result):
                return (result)
        return (None)

    def update(self, dt: float) -> None:
        pass

    def draw(self, renderer: PygameRenderer):
        renderer.clear((0, 0, 0))
        renderer.draw_text("HIGHSCORES", 190, 40, (255, 255, 255), big=True)

        if (not self.scores):
            renderer.draw_text("Aucun score enregistrer",
                               170, 150, (255, 255, 255))
        else:
            y = 120
            for rank, (name, score) in enumerate(self.scores[:10], start=1):
                line = f"{rank}. {name} - {score}"
                renderer.draw_text(line, 200, y, (255, 255, 255))
                y += 30
        self.back_button.draw(renderer)
