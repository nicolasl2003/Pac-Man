"""A ghost chasing a player who stands still must not pace the same cells.

Only the ghosts tick here, the player never moves. A trail that crosses the
player is a catch; a trail that keeps repeating the same cells without ever
crossing it is a loop. Hardcore must never loop. Normal loops on some
ghosts are a warning, and on every ghost of the level they are a bug.
"""

import warnings
from typing import Callable

import pytest

from src import GameState

_SEEDS: list[int] = [*range(1, 21), 42]
_TICKS = 300
_TAIL = 60
_LONGEST_LOOP = 12


def _loop_length(trail: list[tuple[int, int]],
                 player: tuple[int, int]) -> int:
    """Returns the length of the loop a trail ends in, 0 when it has none.

    trail -- the cells a ghost stood on, one per tick
    player -- the cell of the player, which a catch would have crossed
    """

    tail = trail[-_TAIL:]
    if player in tail:
        return 0
    for length in range(2, _LONGEST_LOOP + 1):
        if all(tail[index] == tail[index + length]
               for index in range(len(tail) - length)):
            return length
    return 0


def _loop_lengths(seed: int, difficulty: str,
                  write_config: Callable[[str], str]) -> list[int]:
    """Returns the loop length of each ghost of a fresh level, 0 for none.

    seed -- the seed of the maze the level is generated from
    difficulty -- the ghost_chase value of the config
    write_config -- the fixture writing a config file
    """

    from src import Config

    Config.load_from_file(write_config(
        f'{{"seed": {seed}, "ghost_chase": "{difficulty}"}}'))
    GameState.reset()
    level = GameState.level
    trails: list[list[tuple[int, int]]] = [[] for _ in level.ghosts]
    for _ in range(_TICKS):
        for trail, ghost in zip(trails, level.ghosts):
            ghost.tick()
            trail.append(ghost.cell.pos)
    return [_loop_length(trail, level.player.cell.pos) for trail in trails]


@pytest.mark.parametrize("seed", _SEEDS)
def test_a_hardcore_ghost_never_paces_around_a_still_player(
        seed: int, write_config: Callable[[str], str]) -> None:
    """The shortest path ends on the player, it is never walked in circles."""

    lengths = _loop_lengths(seed, "Hardcore", write_config)

    assert lengths
    assert not any(lengths), f"ghost loop lengths {lengths}"


@pytest.mark.parametrize("seed", _SEEDS)
def test_a_normal_ghost_reaches_a_still_player_even_when_others_pace(
        seed: int, write_config: Callable[[str], str]) -> None:
    """At least one Normal ghost reaches a player who stands still.

    Some ghosts looping is only worth a warning.
    """

    lengths = _loop_lengths(seed, "Normal", write_config)
    pacing = sum(1 for length in lengths if length)

    if pacing:
        warnings.warn(f"{pacing} of {len(lengths)} Normal ghosts pace "
                      f"around a still player (seed {seed}, "
                      f"loop lengths {lengths})", stacklevel=1)
    assert lengths
    assert pacing < len(lengths)
