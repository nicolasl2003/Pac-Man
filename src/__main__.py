from .renderer import PygameRenderer
import sys


def main() -> None:
    renderer = PygameRenderer(640, 480, "Pac-Man 42")
    running = True

    while (running):
        actions = renderer.poll_events()
        for action in actions:
            if (action in ("QUIT", "ESCAPE")):
                running = False
        renderer.clock.tick(60)

    renderer.close()


if (__name__ == "__main__"):
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(1)
