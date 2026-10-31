"""The cheat mode runs the game faster, for whoever reviews it."""

from typing import Callable, Iterator

import pytest

from src import Config, GameState

from capabilities import has_a_cheat_tick, speeds_up_when_cheating
from gaps import known_bug, missing
from review import verifies


@pytest.fixture(autouse=True)
def plain_game() -> Iterator[None]:
    """Leaves the cheat mode off behind every test of this file."""

    yield
    GameState.cheat = False


@missing("a tick the game state owns", when=not has_a_cheat_tick(),
         raises=AttributeError)
@verifies("src.game_state.GameStateModel.tick_ms")
def test_a_vanilla_tick_lasts_what_the_config_asks() -> None:
    """Off the cheat mode, a tick is the one the config asks for."""

    assert GameState.tick_ms == Config.ms_per_tick


@missing("a tick the game state owns", when=not has_a_cheat_tick(),
         raises=AttributeError)
@pytest.mark.parametrize("ticks_per_sec", [1, 4, 10, 11, 1000])
@verifies("src.game_state.GameStateModel.tick_ms")
def test_cheating_never_slows_the_game_down(
        write_config: Callable[[str], str], ticks_per_sec: int) -> None:
    """A cheating tick is playable, whatever the config asks for.

    A tick of zero divides by zero in the game loop, a negative one hangs it.
    """

    Config.load_from_file(
        write_config(f'{{"ticks_per_sec": {ticks_per_sec}}}'))
    GameState.cheat = True

    assert 1 <= GameState.tick_ms <= Config.ms_per_tick


@known_bug("the cheat mode leaves a tick as long as a vanilla one",
           when=not speeds_up_when_cheating(),
           raises=(AttributeError, AssertionError))
@verifies("src.game_state.GameStateModel.tick_ms")
def test_cheating_shortens_a_tick_by_a_tenth_of_a_second() -> None:
    """The cheat mode takes 100ms off the tick of the default config."""

    GameState.cheat = True

    assert GameState.tick_ms == Config.ms_per_tick - 100


@known_bug("the cheat mode leaves a tick as long as a vanilla one",
           when=not speeds_up_when_cheating(),
           raises=(AttributeError, AssertionError))
@verifies("src.game_state.GameStateModel.tick_ms")
def test_the_cheat_tick_keeps_its_floor(
        write_config: Callable[[str], str]) -> None:
    """A tick the full 100ms would empty stops at its floor instead."""

    Config.load_from_file(write_config('{"ticks_per_sec": 10}'))
    GameState.cheat = True

    assert GameState.tick_ms == 80


@known_bug("the cheat mode leaves a tick as long as a vanilla one",
           when=not speeds_up_when_cheating(),
           raises=(AttributeError, AssertionError))
@verifies("src.game_state.GameStateModel.timer_s")
def test_the_timer_counts_real_seconds_while_cheating() -> None:
    """The shorter tick of the cheat mode shows on the clock of the HUD."""

    vanilla: int = GameState.timer_s
    GameState.cheat = True

    assert GameState.timer_s < vanilla
