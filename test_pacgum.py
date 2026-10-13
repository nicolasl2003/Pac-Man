"""Pacgums are the collectables that end a level once cleared."""

from typing import Callable

from src import Config, GameState, Ghost, Level, PacGum, SuperPacGum

from gaps import missing


def _plain_gums(level: Level) -> list[PacGum]:
    """Returns the pacgums of a level that are not super ones.

    level -- the level to read
    """

    return [gum for gum in level.pacgums
            if not isinstance(gum, SuperPacGum)]


def test_a_new_level_lays_pacgums_on_open_cells(
        open_level: Callable[..., Level]) -> None:
    """Every pacgum sits on a reachable cell, one per cell."""

    level = open_level(11, 11)

    assert level.pacgums
    assert all(gum.cell.accessible for gum in level.pacgums)
    assert len({gum.cell.pos for gum in level.pacgums}) == len(level.pacgums)


def test_the_configured_counts_are_laid_down(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """The config decides how many of each kind a level holds."""

    Config.load_from_file(write_config('{"pacgum_count": 20}'))
    level = open_level(11, 11)
    supers = [gum for gum in level.pacgums if isinstance(gum, SuperPacGum)]

    assert len(_plain_gums(level)) == Config.pacgum_count
    assert len(supers) == Config.super_pacgum_count


def test_minus_one_fills_every_free_cell(
        open_level: Callable[..., Level]) -> None:
    """The default -1 lays a pacgum everywhere but under the player."""

    level = open_level(11, 11)

    assert Config.pacgum_count == -1
    assert len(level.pacgums) == 11 * 11 - 1


def test_super_pacgums_sit_in_the_four_corners(
        open_level: Callable[..., Level]) -> None:
    """The power pellets are the corners of the maze."""

    level = open_level(11, 11)
    supers = [gum for gum in level.pacgums if isinstance(gum, SuperPacGum)]

    assert {gum.cell.pos for gum in supers} == {(0, 0), (10, 0),
                                                (0, 10), (10, 10)}


def test_a_pacgum_is_worth_the_configured_points(
        open_level: Callable[..., Level]) -> None:
    """Each kind carries the prize its config key names."""

    level = open_level(11, 11)
    supers = [gum for gum in level.pacgums if isinstance(gum, SuperPacGum)]

    assert _plain_gums(level)[0].prize == Config.pacgum_points
    assert supers[0].prize == Config.ss_pacgum_points


def test_a_pacgum_registers_on_its_cell(
        open_level: Callable[..., Level]) -> None:
    """The player finds the pacgums through the cell it stands on."""

    level = open_level(11, 11)
    gum = _plain_gums(level)[0]

    assert gum in gum.cell.entities


def test_the_player_does_not_start_on_a_pacgum(
        open_level: Callable[..., Level]) -> None:
    """The spawn cell is left empty, so no free point on frame one."""

    level = open_level(11, 11)

    assert level.player.cell.pos not in {gum.cell.pos
                                         for gum in level.pacgums}


@missing("Player.tick, which eats what the player stands on")
def test_walking_over_a_pacgum_scores_and_clears_it(
        open_level: Callable[..., Level]) -> None:
    """Eating adds the configured points and removes the pacgum."""

    level = open_level(11, 11)
    level.ghosts.clear()
    gum = _plain_gums(level)[0]
    level.player.cell = gum.cell
    before = GameState.score

    level.tick()

    assert GameState.score == before + Config.pacgum_points
    assert gum not in level.pacgums


@missing("Player.tick, which eats what the player stands on")
def test_a_pacgum_is_only_eaten_once(
        open_level: Callable[..., Level]) -> None:
    """Staying on the cleared cell does not keep scoring."""

    level = open_level(11, 11)
    level.ghosts.clear()
    level.player.cell = _plain_gums(level)[0].cell
    level.tick()
    scored = GameState.score

    level.tick()

    assert GameState.score == scored


@missing("Player.tick frightening the ghosts on a super pacgum")
def test_a_super_pacgum_scores_more_and_frightens_the_ghosts(
        open_level: Callable[..., Level]) -> None:
    """The power pellet is worth its own points and turns the ghosts."""

    level = open_level(11, 11)
    for ghost in level.ghosts:
        ghost.cell = level.maze.get_cell(5, 5)
    sup = next(gum for gum in level.pacgums
               if isinstance(gum, SuperPacGum) and gum.cell.pos == (0, 0))
    level.player.cell = sup.cell
    before = GameState.score

    level.tick()

    assert GameState.score == before + Config.ss_pacgum_points
    assert all(ghost.mode is Ghost.GhostMode.EDIBLE
               for ghost in level.ghosts)


@missing("the won state, set when the last pacgum is eaten")
def test_clearing_every_pacgum_wins_the_level(
        write_config: Callable[[str], str],
        open_level: Callable[..., Level]) -> None:
    """The level is won when nothing is left to eat."""

    Config.load_from_file(write_config('{"level_time": 500}'))
    level = open_level(9, 9)
    level.ghosts.clear()

    for gum in list(level.pacgums):
        level.player.cell = gum.cell
        level.tick()

    assert not level.pacgums
    assert level.state is Level.State.WON
