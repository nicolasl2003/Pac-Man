from typing import Optional, Any
from manage_screen.screen import Screen
from manage_screen.button import Button
import pygame
from ..scores import load_scores


class HighscoresScreen(Screen):
    def __init__(self) -> None:
        self.buttons: list[Button] = []
        self.scores: list[tuple[str, int]] = []

    def on_enter(self, **kwargs: Any) -> None:
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
        screen_width = renderer.width
        screen_height = renderer.height

        width = int(screen_width * width_ratio)
        height = int(screen_height * height_ratio)
        x = int(screen_width * x_ratio) - width // 2
        y = int(screen_height * y_ratio) - height // 2

        return (Button(x=x, y=y, width=width, height=height,
                       text=text, action=action))

    def handle_events(self, events: list[Any]) -> Optional[str]:
        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")
            if (event.kind == "KEY" and event.key == "ESCAPE"):
                return ("QUIT")

            for button in self.buttons:
                result = button.handle_event(event)
                if (result):
                    return (result)
        return (None)

    def update(self, dt: float) -> None:
        pass

    def draw(self, renderer: Any) -> None:
        renderer.clear((0, 0, 0))
        screen_width = renderer.width
        title_surface = self.title_font.render("HIGHSCORES",
                                               True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(screen_width // 2, 60))
        renderer.screen.blit(title_surface, title_rect)

        if (not self.scores):
            no_score_surface = self.score_font.render(
                "Aucun score enregistrer", True, (255, 255, 255)
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
