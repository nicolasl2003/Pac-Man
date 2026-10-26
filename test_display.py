"""The graphic layer starts on any machine, with or without devices.

The layer lives in manage_screen, so these tests drive it through the
dummy SDL drivers a CI runner has, never a real screen.
"""

import os
import subprocess
import sys
from typing import Iterator

import pygame
import pytest

from manage_screen.renderer import PygameRenderer
from src import Config

from capabilities import reports_a_missing_video_device
from gaps import missing
from helpers import ROOT


@pytest.fixture(autouse=True)
def fresh_pygame() -> Iterator[None]:
    """Shuts pygame down around each test, so SDL rereads its drivers."""

    pygame.quit()
    yield
    pygame.quit()


def test_importing_the_game_does_not_open_a_window() -> None:
    """Nothing is initialised before the game asks for it.

    A fresh interpreter is needed: this process has already imported it.
    """

    probe = ("import pygame, src, manage_screen.renderer;"
             "print(pygame.display.get_init(), pygame.display.get_surface())")

    run = subprocess.run([sys.executable, "-c", probe], cwd=ROOT,
                         env={**os.environ, "PYGAME_HIDE_SUPPORT_PROMPT": "1"},
                         capture_output=True, text=True, timeout=30)

    assert run.returncode == 0, run.stderr
    assert run.stdout.splitlines()[-1] == "False None"


def test_starting_uses_the_given_size() -> None:
    """The window is the size the caller asked for."""

    renderer = PygameRenderer(320, 240, "test")

    assert (renderer.width, renderer.height) == (320, 240)
    assert renderer.screen.get_size() == (320, 240)


def test_the_configured_size_is_usable() -> None:
    """The size the config carries opens a window."""

    renderer = PygameRenderer(Config.screen_width, Config.screen_height,
                              "test")

    assert renderer.screen.get_size() == (Config.screen_width,
                                          Config.screen_height)


@missing("an error the caller can handle when no video device answers",
         when=not reports_a_missing_video_device(),
         raises=SystemExit)
def test_a_missing_video_device_is_reported(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """A machine without a screen gets an error, not an exit."""

    monkeypatch.setenv("SDL_VIDEODRIVER", "pacman-has-no-such-driver")

    with pytest.raises(pygame.error):
        PygameRenderer(100, 100, "test")


def test_a_missing_sound_device_does_not_stop_the_game(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Sound is optional: the game runs on a mute machine."""

    monkeypatch.setenv("SDL_AUDIODRIVER", "pacman-has-no-such-driver")

    renderer = PygameRenderer(100, 100, "test")

    assert renderer.screen.get_size() == (100, 100)
    assert pygame.mixer.get_init() is None


def test_a_working_sound_device_is_used(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """When a device answers, the mixer is ready."""

    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")

    PygameRenderer(100, 100, "test")

    assert pygame.mixer.get_init() is not None


def test_drawing_a_frame_needs_no_real_screen() -> None:
    """A frame can be drawn on the dummy driver, as in a CI run."""

    renderer = PygameRenderer(100, 100, "test")

    renderer.clear()
    renderer.draw_text("42", 10, 10)
    renderer.present()


def test_clearing_blanks_the_window() -> None:
    """A cleared window holds the background colour only."""

    renderer = PygameRenderer(40, 40, "test")
    renderer.draw_rect(0, 0, 10, 10, (255, 0, 0))

    renderer.clear()

    assert renderer.screen.get_at((5, 5)) == pygame.Color(0, 0, 0)


def test_a_rectangle_fills_its_pixels() -> None:
    """The hand-made rectangle paints every pixel it covers."""

    renderer = PygameRenderer(40, 40, "test")

    renderer.draw_rect(5, 5, 10, 10, (10, 20, 30))

    assert renderer.screen.get_at((5, 5)) == pygame.Color(10, 20, 30)
    assert renderer.screen.get_at((14, 14)) == pygame.Color(10, 20, 30)
    assert renderer.screen.get_at((15, 15)) != pygame.Color(10, 20, 30)


def test_a_line_touches_both_of_its_ends() -> None:
    """The hand-made line starts and stops where it was told."""

    renderer = PygameRenderer(40, 40, "test")

    renderer.draw_line((2, 2), (2, 20), (1, 2, 3))

    assert renderer.screen.get_at((2, 2)) == pygame.Color(1, 2, 3)
    assert renderer.screen.get_at((2, 20)) == pygame.Color(1, 2, 3)


def test_a_line_of_no_length_draws_one_pixel() -> None:
    """Two identical ends must not divide by zero."""

    renderer = PygameRenderer(40, 40, "test")

    renderer.draw_line((3, 3), (3, 3), (4, 5, 6))

    assert renderer.screen.get_at((3, 3)) == pygame.Color(4, 5, 6)


def test_measuring_text_gives_a_positive_size() -> None:
    """The button layout needs the width of its label."""

    renderer = PygameRenderer(40, 40, "test")

    width, height = renderer.get_text_size("PACMAN", 24)

    assert width > 0
    assert height > 0


def test_loading_a_missing_image_is_reported() -> None:
    """A missing asset raises an error the screens catch."""

    renderer = PygameRenderer(40, 40, "test")

    with pytest.raises(OSError):
        renderer.load_image(str(ROOT / "src/img/there-is-no-such-image.png"))


def test_loading_an_image_caches_it() -> None:
    """The same asset is only read from the disk once."""

    renderer = PygameRenderer(40, 40, "test")
    path = str(ROOT / "src/img/logo.png")
    if not os.path.exists(path):
        pytest.skip("the image assets are not in this checkout")

    assert renderer.load_image(path) is renderer.load_image(path)


def test_polling_without_an_event_gives_an_empty_list() -> None:
    """A quiet frame reports nothing."""

    renderer = PygameRenderer(40, 40, "test")

    assert renderer.poll_events() == []


def test_a_key_press_is_reported() -> None:
    """A known key arrives as a KEY event."""

    renderer = PygameRenderer(40, 40, "test")
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,
                                         key=pygame.K_ESCAPE))

    events = renderer.poll_events()

    assert [(event.kind, event.key) for event in events] == [("KEY",
                                                              "ESCAPE")]


def test_an_unknown_key_is_dropped() -> None:
    """A key the game does not use is not reported."""

    renderer = PygameRenderer(40, 40, "test")
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F13))

    assert renderer.poll_events() == []


def test_closing_the_window_is_reported() -> None:
    """The window manager asking to quit reaches the game."""

    renderer = PygameRenderer(40, 40, "test")
    pygame.event.post(pygame.event.Event(pygame.QUIT))

    assert [event.kind for event in renderer.poll_events()] == ["QUIT"]


def test_a_left_click_is_reported_with_its_position() -> None:
    """The buttons need where the pointer was."""

    renderer = PygameRenderer(40, 40, "test")
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         button=1, pos=(7, 9)))

    events = renderer.poll_events()

    assert [(event.kind, event.pos) for event in events] == [("CLICK",
                                                              (7, 9))]


def test_stopping_releases_the_window() -> None:
    """A closed renderer leaves no window behind."""

    renderer = PygameRenderer(40, 40, "test")

    renderer.close()

    assert pygame.display.get_surface() is None


def test_stopping_is_idempotent() -> None:
    """Closing twice is harmless."""

    renderer = PygameRenderer(40, 40, "test")

    renderer.close()
    renderer.close()

    assert pygame.display.get_surface() is None
