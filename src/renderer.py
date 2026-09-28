import pygame


class PygameRenderer:
    def __init__(self, width: int, height: int, title: str):
        pygame.init()
        self.width: int = width
        self.height: int = height
        self.screen: pygame.Surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock: pygame.time.Clock = pygame.time.Clock()

    def poll_events(self) -> list[str]:
        actions: list[str] = []
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                actions.append("QUIT")
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                actions.append("ESCAPE")
        return (actions)

    def close(self) -> None:
        pygame.quit()
