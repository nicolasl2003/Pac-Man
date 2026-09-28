import pygame

Color = tuple[int, int, int]


class PygameRenderer:
    def __init__(self, width: int, height: int, title: str):
        pygame.init()
        self.width: int = width
        self.height: int = height
        self.screen: pygame.Surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock: pygame.time.Clock = pygame.time.Clock()

        try:
            self.font: pygame.font.Font = pygame.font.SysFont("arial", 24)
            self.font_big: pygame.font.Font = pygame.font.SysFont("arial", 48)
        except pygame.error:
            self.font = pygame.font.Font(None, 24)
            self.font_big = pygame.font.Font(None, 48)

    def poll_events(self) -> list[str]:
        actions: list[str] = []
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                actions.append("QUIT")
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                actions.append("ESCAPE")
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                actions.append("ENTER")
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_UP):
                actions.append("UP")
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN):
                actions.append("DOWN")
        return (actions)

    def clear(self, color: Color = (0, 0, 0)) -> None:
        self.screen.fill(color)

    def draw_rect(self, x: int, y: int, width: int, height: int, color: Color) -> None:
        pygame.draw.rect(self.screen, color, (x, y, width, height))

    def draw_text(self,
                  text: str,
                  x: int,
                  y: int,
                  color: Color = (255, 255, 255),
                  big: bool = False) -> None:
        font = self.font_big if big else self.font
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def present(self) -> None:
        pygame.display.flip()

    def close(self) -> None:
        pygame.quit()
