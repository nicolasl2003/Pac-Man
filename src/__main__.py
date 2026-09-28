from .renderer import PygameRenderer
from .button import Button
import pygame
import sys


def main() -> None:
    renderer = PygameRenderer(640, 480, "Pac-Man 42")
    button = Button(220, 200, 200, 60, "START", action="START")
    running = True

    while (running):
        for event in renderer.poll_events():
            if (event.kind == "QUIT" or (event.kind == "KEY" and event.key == "ESPAPE")):
                running = False
            result = button.handle_event(event)
            if (result):
                print(f"Button cliquer : {result}")

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
