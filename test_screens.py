"""The screens route the player between the menus and the game.

They load their images and sounds from paths relative to the project
root, so every test runs from there, on the dummy SDL drivers.
"""

import subprocess
import sys
from typing import Iterator

import pygame
import pytest

from manage_screen.button import Button
from manage_screen.renderer import InputEvent, PygameRenderer
from src import Config, GameState
from src.screens.game import Games
from src.screens.highscores import HighscoresScreen
from src.screens.main_menu import MainMenuScreen

from helpers import ROOT
from review import verifies


@pytest.fixture
def renderer(monkeypatch: pytest.MonkeyPatch) -> Iterator[PygameRenderer]:
    """Opens the configured window from the project root."""

    monkeypatch.chdir(ROOT)
    yield PygameRenderer(Config.screen_width, Config.screen_height, "test")
    pygame.quit()


def _click(button: Button) -> InputEvent:
    """Returns a left click in the middle of a button.

    button -- the button to click
    """

    return InputEvent(kind="CLICK", pos=(button.x + button.width // 2,
                                         button.y + button.height // 2))


@verifies("src.screens.main_menu.MainMenuScreen.on_enter")
def test_every_menu_button_fits_in_the_window(
        renderer: PygameRenderer) -> None:
    """QUIT used to be drawn below the bottom of the window."""

    menu = MainMenuScreen()
    menu.on_enter(renderer=renderer)

    assert all(0 <= button.y and button.y + button.height <= renderer.height
               for button in menu.buttons)


@verifies("src.screens.main_menu.MainMenuScreen.handle_events")
def test_start_opens_the_game(renderer: PygameRenderer) -> None:
    """START is the button that hands the loop over to the game."""

    menu = MainMenuScreen()
    menu.on_enter(renderer=renderer)
    start = next(button for button in menu.buttons if button.text == "START")

    assert menu.handle_events([_click(start)]) == "GAME"


@verifies("src.screens.main_menu.MainMenuScreen.on_enter")
def test_entering_the_menu_starts_a_new_run(
        renderer: PygameRenderer) -> None:
    """Coming back to the menu is what clears the score of a run."""

    GameState.score = 500

    MainMenuScreen().on_enter(renderer=renderer)

    assert GameState.score == 0


@verifies("src.screens.game.Games.on_enter")
def test_entering_the_game_keeps_the_run(renderer: PygameRenderer) -> None:
    """Resuming from the pause keeps the level that was being played."""

    game = Games()
    level = GameState.level

    game.on_enter(renderer=renderer)

    assert GameState.level is level


@verifies("src.screens.end.EndScreen.handle_events")
def test_closing_the_window_on_the_end_screen_quits(
        renderer: PygameRenderer) -> None:
    """The close button of the window works on every screen."""

    from src.screens.end import EndScreen

    assert EndScreen().handle_events([InputEvent(kind="QUIT")]) == "QUIT"


@verifies("src.screens.highscores.HighscoresScreen.handle_events")
def test_escape_on_the_highscores_goes_back_to_the_menu(
        renderer: PygameRenderer) -> None:
    """Escape leaves the table instead of closing the game."""

    scores = HighscoresScreen()
    scores.on_enter(renderer=renderer)

    assert scores.handle_events(
        [InputEvent(kind="KEY", key="ESCAPE")]) == "MENU"


@verifies("src.screens.game.Games.draw")
def test_the_hud_is_drawn_above_the_maze(renderer: PygameRenderer) -> None:
    """Score, lives, level and time are written in the top margin."""

    game = Games()
    game.on_enter(renderer=renderer)
    game.draw(renderer)
    wall: pygame.Color = pygame.Color(0, 0, 255)
    maze_top: int = next(y for y in range(renderer.height)
                         if any(renderer.screen.get_at((x, y)) == wall
                                for x in range(renderer.width)))

    assert any(renderer.screen.get_at((x, y)) != pygame.Color(0, 0, 0)
               for x in range(renderer.width) for y in range(maze_top))


@pytest.mark.parametrize("key, name", [(pygame.K_z, "Z"),
                                       (pygame.K_q, "Q"),
                                       (pygame.K_p, "P"),
                                       (pygame.K_7, "7"),
                                       (pygame.K_SPACE, " "),
                                       (pygame.K_BACKSPACE, "BACKSPACE")])
@verifies("manage_screen.renderer.PygameRenderer._translate_key")
def test_a_letter_key_is_reported_as_its_letter(renderer: PygameRenderer,
                                                key: int, name: str) -> None:
    """A name is typed with the same keys that drive the player."""

    assert renderer._translate_key(key) == name


@pytest.mark.parametrize("arguments", [[], ["a.json", "b.json"]])
@verifies("src.__main__.run")
def test_the_game_wants_exactly_one_config_file(
        arguments: list[str]) -> None:
    """pac-man.py prints its usage and exits with 2 otherwise."""

    run = subprocess.run([sys.executable, "pac-man.py", *arguments],
                         cwd=ROOT, capture_output=True, text=True,
                         timeout=30)

    assert run.returncode == 2
    assert "usage:" in run.stderr
