from dataclasses import dataclass
import pygame
from typing import Optional
from .sound import quit_sound
import sys

Color = tuple[int, int, int]


@dataclass
class InputEvent:
    """Represent a normalized keyboard or mouse input event."""

    kind: str
    key: Optional[str] = None
    pos: Optional[tuple[int, int]] = None


class PygameRenderer:
    """Initialize the Pygame window and provide common drawing operations."""

    def __init__(self, width: int, height: int, title: str):
        """Initialize the window, clock, and default fonts.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            title: Window title.
        """
        try:
            pygame.init()
            self.width: int = width
            self.height: int = height
            self.screen: pygame.Surface = pygame.display.set_mode((width,
                                                                   height))
            pygame.display.set_caption(title)
            self.clock: pygame.time.Clock = pygame.time.Clock()
            self._image_cache: dict[str, pygame.Surface] = {}
        except pygame.error as e:
            print(e)
            sys.exit(1)
        try:
            self.font: pygame.font.Font = pygame.font.SysFont("arial", 24)
            self.font_big: pygame.font.Font = pygame.font.SysFont("arial", 48)
        except pygame.error:
            self.font = pygame.font.Font(None, 24)
            self.font_big = pygame.font.Font(None, 48)

    def load_image(self, path: str) -> pygame.Surface:
        """Load an image with transparency and cache it for reuse.

        Args:
            path: Path to the image file.

        Returns:
            The loaded Pygame image surface.

        Raises:
            IOError: If the image file does not exist.
        """
        if (path in self._image_cache):
            return (self._image_cache[path])
        try:
            image = pygame.image.load(path).convert_alpha()
            self._image_cache[path] = image
        except pygame.error as exc:
            raise IOError(
                f"Failed to parse file '{path}' to image: {exc}"
            )
        return (image)

    def draw_image(self, image: pygame.Surface, x: int, y: int,
                   width: int, height: int, centered: bool = True) -> None:
        """Draw an image at the specified position.

        Args:
            image: Pygame image surface to draw.
            x: Horizontal coordinate of the top-left corner.
            y: Vertical coordinate of the top-left corner.
        """
        scaled = self.scale_image(image, width, height)
        if (centered):
            x = x - width // 2
            y = y - height // 2
        self.screen.blit(scaled, (x, y))

    def scale_image(self, image: pygame.Surface, width: int, height:
                    int) -> pygame.Surface:
        """Resize an image using smooth scaling.

        Args:
            image: Pygame image surface to resize.
            width: Target width in pixels.
            height: Target height in pixels.

        Returns:
            A new surface with the requested dimensions.
        """
        return (pygame.transform.smoothscale(image, (width, height)))

    def center_image(self, image: pygame.Surface, center_x: int, center_y:
                     int) -> None:
        """Draw an image centered at the supplied coordinates.

        Args:
            image: Pygame image surface to draw.
            center_x: Horizontal coordinate of the image center.
            center_y: Vertical coordinate of the image center.
        """
        rect = image.get_rect(center=(center_x, center_y))
        self.screen.blit(image, rect)

    def draw_scaled_centered(self, image: pygame.Surface, new_w: int,
                             new_h: int) -> None:
        old_w, old_h = image.get_size()
        result = pygame.Surface((new_w, new_h), pygame.SRCALPHA)

        for y in range(new_h):
            src_y = y * old_h // new_h
            for x in range(new_w):
                src_x = x * old_w // new_w
                result.set_at((x, y), image.get_at((src_x, src_y)))

    def poll_events(self) -> list[InputEvent]:
        """Collect Pygame events and convert recognized ones to input events.

        Returns:
            The list of recognized user input events.
        """
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
        """Map a Pygame key code to the game's key identifier.

        Args:
            key: Pygame key code.

        Returns:
            The internal key name, or None if the key is unsupported.
        """
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

    def clear(self) -> None:
        """Fill the window surface with the specified color.

        Args:
            color: RGB fill color.
        """
        self.screen.fill((0, 0, 0))

    def draw_rect(self, x: int, y: int,
                  width: int, height: int, color: Color) -> None:
        """Draw a solid rectangle in the specified color.

        Args:
            x: Horizontal coordinate of the top-left corner.
            y: Vertical coordinate of the top-left corner.
            width: Rectangle width in pixels.
            height: Rectangle height in pixels.
            color: RGB rectangle color.
        """
        for i in range(x, x + width):
            for j in range(y, y + height):
                self.screen.set_at((i, j), color)

    def draw_text(self,
                  text: str,
                  x: int,
                  y: int,
                  color: Color = (255, 255, 255),
                  font_size: Optional[int] = None,
                  big: bool = False) -> None:
        """Render text at the specified position.

        Args:
            text: Text to display.
            x: Horizontal coordinate of the text.
            y: Vertical coordinate of the text.
            color: RGB text color.
            font_size: Explicit font size, if required.
            big: Whether to use the default large font.
        """
        if (font_size is not None):
            font = pygame.font.SysFont("arial", font_size)
        else:
            font = self.font_big if big else self.font
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def get_text_size(self, text: str, font_size: int = 24) -> tuple[int, int]:
        """Measure the rendered dimensions of a string.

        Args:
            text: Text to measure.
            font_size: Font size in points.

        Returns:
            The text width and height in pixels.
        """
        font = pygame.font.SysFont("arial", font_size)
        surface = font.render(text, True, (0, 0, 0))
        return (surface.get_width(), surface.get_height())

    def draw_line(self, start: tuple[int, int], end: tuple[int, int],
                  color: Color) -> None:
        """Draw a line segment between two points.

        Args:
            start: Coordinates of the starting point.
            end: Coordinates of the ending point.
            color: RGB line color.
            width: Line thickness in pixels.
        """
        x0, y0 = start
        x1, y1 = end
        steps = max(abs(x1 - x0), abs(y1 - y0))

        for i in range(steps + 1):
            t = i / steps if steps > 0 else 0
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            self.screen.set_at((x, y), color)

    def present(self) -> None:
        """Update the display with the contents of the window surface."""
        pygame.display.flip()

    def close(self) -> None:
        """Stop audio playback and shut down Pygame resources."""
        print("stop the music")
        quit_sound()
        pygame.quit()
