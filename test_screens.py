"""The screens route the player between the menus and the game.

They load their images and sounds from paths relative to the project
root, so every test runs from there, on the dummy SDL drivers.
"""

import subprocess
import sys
from pathlib import Path
from typing import Iterator

import pygame
import pytest

from manage_screen.button import Button
from manage_screen.renderer import InputEvent, PygameRenderer
from src import Config, GameState
from src.screens.game import Games
from src.screens.game_over import GameOverScreen
from src.screens.highscores import HighscoresScreen
from src.screens.main_menu import MainMenuScreen

ROOT = Path(__file__).resolve().parent.parent


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


def test_every_menu_button_fits_in_the_window(
        renderer: PygameRenderer) -> None:
    """QUIT used to be drawn below the bottom of the window."""

    menu = MainMenuScreen()
    menu.on_enter(renderer=renderer)

    assert all(0 <= button.y and button.y + button.height <= renderer.height
               for button in menu.buttons)


def test_start_asks_for_a_new_game(renderer: PygameRenderer) -> None:
    """START sends the data that makes the game screen reset the run."""

    menu = MainMenuScreen()
    menu.on_enter(renderer=renderer)
    start = next(button for button in menu.buttons if button.text == "START")

    assert menu.handle_events([_click(start)]) == ("GAME", {"new_game": True})


def test_only_a_new_game_resets_the_run(renderer: PygameRenderer) -> None:
    """Resuming from the pause keeps the level, a new game replaces it."""

    game = Games()
    level = GameState.level

    game.on_enter(renderer=renderer)
    assert GameState.level is level

    game.on_enter(renderer=renderer, new_game=True)
    assert GameState.level is not level


def test_the_game_over_menu_button_goes_to_the_menu(
        renderer: PygameRenderer) -> None:
    """MENU used to sit under REJOUER and was never checked."""

    over = GameOverScreen()

    assert over.handle_events([_click(over.menu_button)]) == "MENU"
    assert over.handle_events([_click(over.retry_button)]) == (
        "GAME", {"new_game": True})


def test_closing_the_window_on_game_over_quits(
        renderer: PygameRenderer) -> None:
    """The close button of the window works on every screen."""

    assert GameOverScreen().handle_events([InputEvent(kind="QUIT")]) == "QUIT"


def test_escape_on_the_highscores_goes_back_to_the_menu(
        renderer: PygameRenderer) -> None:
    """Escape leaves the table instead of closing the game."""

    scores = HighscoresScreen()
    scores.on_enter(renderer=renderer)

    assert scores.handle_events(
        [InputEvent(kind="KEY", key="ESCAPE")]) == "MENU"


def test_the_hud_is_drawn_above_the_maze(renderer: PygameRenderer) -> None:
    """Score, lives, level and time are written in the top margin."""

    game = Games()
    game.on_enter(renderer=renderer)
    game.draw(renderer)

    assert any(renderer.screen.get_at((x, y)) != pygame.Color(0, 0, 0)
               for x in range(0, 300) for y in range(5, 25))


@pytest.mark.parametrize("key, name", [(pygame.K_z, "UP"),
                                       (pygame.K_q, "LEFT"),
                                       (pygame.K_p, "PAUSE")])
def test_zqsd_and_pause_keys_are_translated(renderer: PygameRenderer,
                                            key: int, name: str) -> None:
    """AZERTY players move with ZQSD, and P pauses the game."""

    assert renderer._translate_key(key) == name


@pytest.mark.parametrize("arguments", [[], ["a.json", "b.json"]])
def test_the_game_wants_exactly_one_config_file(
        arguments: list[str]) -> None:
    """pac-man.py prints its usage and exits with 2 otherwise."""

    run = subprocess.run([sys.executable, "pac-man.py", *arguments],
                         cwd=ROOT, capture_output=True, text=True,
                         timeout=30)

    assert run.returncode == 2
    assert "usage:" in run.stderr
