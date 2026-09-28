from .renderer import PygameRenderer
from .screen import Screen
from .screens.main_menu import MainMenuScreen
import sys


def main() -> None:
    renderer = PygameRenderer(640, 480, "Pac-Man 42")

    screens: dict[str, Screen] = {
        "MENU": MainMenuScreen(),
    }
    current: str = "MENU"
    running = True

    while (running):
        events = renderer.poll_events()
        next_screen = screens[current].handle_events(events)
        if (next_screen == "QUIT"):
            running = False
        elif (next_screen is not None):
            if (next_screen in screens):
                current = next_screen
            else:
                print(f"[WARN] Ecran '{next_screen}' pas encore implemter.")

        screens[current].update(renderer.clock.get_time() / 1000.0)
        screens[current].draw(renderer)
        renderer.present()

        renderer.clock.tick(60)

    renderer.close()


if (__name__ == "__main__"):
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(1)
