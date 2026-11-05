import sys
from argparse import ArgumentParser

import pygame

from manage_screen.renderer import PygameRenderer
from manage_screen.screen import Screen
from .screens.end import EndScreen
from .screens.game import Games
from .screens.highscores import HighscoresScreen
from .screens.instruction import InstructionsScreen
from .screens.main_menu import MainMenuScreen
from .screens.pause import PauseScreen
from .screens.timeout import TimeoutScreen


def main(config_path: str) -> None:
    """Load the configuration and run the main game loop.

    config_path -- The path of the JSON configuration file
    """

    from . import Config, GameState

    Config.load_from_file(config_path)
    GameState.reset()
    renderer = PygameRenderer(Config.screen_width,
                              Config.screen_height, "Pac-Man 42")
    screens: dict[str, Screen] = {
        "MENU": MainMenuScreen(),
        "HIGHSCORES": HighscoresScreen(),
        "END": EndScreen(),
        "GAME": Games(),
        "INSTRUCTIONS": InstructionsScreen(),
        "PAUSE": PauseScreen(),
        "TIMEOUT": TimeoutScreen()
    }
    current: str = "MENU"
    running = True

    screens[current].on_enter(renderer=renderer)
    while (running):
        events = renderer.poll_events()
        result = screens[current].handle_events(events)

        next_screen = None
        if (isinstance(result, tuple)):
            next_screen, _ = result
        elif (isinstance(result, str)):
            next_screen = result

        if (next_screen == "QUIT"):
            running = False
        elif (next_screen is not None):
            if (next_screen in screens):
                current = next_screen
                screens[current].on_enter(renderer=renderer)
            else:
                print(f"[WARN] Screen '{next_screen}' not yet implemented.",
                      file=sys.stderr)

        screens[current].update(float(renderer.clock.get_time()))
        screens[current].draw(renderer)
        renderer.present()

        renderer.clock.tick(Config.framerate)

    renderer.close()


def run(argv: list[str]) -> None:
    """Checks the command line then runs the game.

    argv -- The command line, the configuration file as only argument
    """

    parser: ArgumentParser = ArgumentParser(prog=f"python3 {argv[0]}")
    parser.add_argument("config", help="path of the JSON configuration file")
    config_path: str = parser.parse_args(argv[1:]).config
    from .config import ConfigError
    from src import AssetError

    try:
        main(config_path)
    except (ConfigError, AssetError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        from signal import SIGINT
        sys.exit(SIGINT)
    except pygame.error as e:
        print(f"Rendering error {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
    else:
        sys.exit(0)
    sys.exit(1)


if (__name__ == "__main__"):
    run(sys.argv)
