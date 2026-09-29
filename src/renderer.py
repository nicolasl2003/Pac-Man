from dataclasses import dataclass
import pygame
from typing import Optional

Color = tuple[int, int, int]


@dataclass
class InputEvent:
    kind: str
    key: Optional[str] = None
    pos: Optional[tuple[int, int]] = None


class PygameRenderer:
    def __init__(self, width: int, height: int, title: str):
        pygame.init()
        self.width: int = width
        self.height: int = height
        self.screen: pygame.Surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self._image_cache: dict[str, pygame.Surface] = {}

        try:
            self.font: pygame.font.Font = pygame.font.SysFont("arial", 24)
            self.font_big: pygame.font.Font = pygame.font.SysFont("arial", 48)
        except pygame.error:
            self.font = pygame.font.Font(None, 24)
            self.font_big = pygame.font.Font(None, 48)

    def load_image(self, path: str) -> pygame.Surface:
        if (path in self._image_cache):
            return (self._image_cache[path])
        try:
            image = pygame.image.load(path).convert_alpha()
            self._image_cache[path] = image
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"File not found '{path}': {exc}"
            )
        return (image)

    def draw_image(self, image: pygame.Surface, x: int, y: int) -> None:
        self.screen.blit(image, (x, y))

    def scale_image(self, image: pygame.Surface, width: int, height:
                    int) -> pygame.Surface:
        return (pygame.transform.smoothscale(image, (width, height)))

    def center_image(self, image: pygame.Surface, center_x: int, center_y:
                     int) -> None:
        rect = image.get_rect(center=(center_x, center_y))
        self.screen.blit(image, rect)

    def poll_events(self) -> list[InputEvent]:
        events: list[InputEvent] = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events.append(InputEvent(kind="QUIT"))

            elif event.type == pygame.KEYDOWN:
                key_name = self._translate_key(event.key)
                if key_name:
                    events.append(InputEvent(kind="KEY", key=key_name))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    events.append(InputEvent(kind="CLICK", pos=event.pos))

            elif event.type == pygame.MOUSEMOTION:
                events.append(InputEvent(kind="MOTION", pos=event.pos))

        return (events)

    def _translate_key(self, key: int) -> Optional[str]:
        mapping = {
            pygame.K_ESCAPE: "ESCAPE",
            pygame.K_UP: "UP",
            pygame.K_DOWN: "DOWN",
            pygame.K_LEFT: "LEFT",
            pygame.K_RIGHT: "RIGHT",
            pygame.K_w: "UP",
            pygame.K_s: "DOWN",
            pygame.K_a: "LEFT",
            pygame.K_d: "RIGHT",
            pygame.K_RETURN: "ENTER",
        }
        return (mapping.get(key))

    def clear(self, color: Color = (0, 0, 0)) -> None:
        self.screen.fill(color)

    def draw_rect(self, x: int, y: int,
                  width: int, height: int, color: Color) -> None:
        pygame.draw.rect(self.screen, color, (x, y, width, height))

    def draw_text(self,
                  text: str,
                  x: int,
                  y: int,
                  color: Color = (255, 255, 255),
                  font_size: Optional[int] = None,
                  big: bool = False) -> None:
        if (font_size is not None):
            font = pygame.font.SysFont("arial", font_size)
        else:
            font = self.font_big if big else self.font
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def get_text_size(self, text: str, font_size: int = 24) -> tuple[int, int]:
        font = pygame.font.SysFont("arial", font_size)
        surface = font.render(text, True, (0, 0, 0))
        return (surface.get_width(), surface.get_height())

    def present(self) -> None:
        pygame.display.flip()

    def close(self) -> None:
        pygame.quit()
