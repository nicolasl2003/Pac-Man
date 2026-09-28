from .renderer import PygameRenderer
from .button import Button
import pygame
import sys


def main() -> None:
    renderer = PygameRenderer(640, 480, "Pac-Man 42")
    button = Button(220, 200, 200, 60, "START", action="START")
    running = True

    while (running):
        actions = renderer.poll_events()
        for action in actions:
            if (action in ("QUIT", "ESCAPE")):
                running = False

        mouse_x, mouse_y = pygame.mouse.get_pos()
        button.update_hover(mouse_x, mouse_y)

        for event in pygame.event.get():
            if (event.type == pygame.MOUSEBUTTONDOWN):
                result = button.handle_click(*event.pos)
                if (result):
                    print(f"Bouton clique {result}")
        renderer.clear((0, 0, 0))
        button.draw(renderer)
        renderer.present()
        renderer.clock.tick(60)

    renderer.close()


if (__name__ == "__main__"):
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(1)
