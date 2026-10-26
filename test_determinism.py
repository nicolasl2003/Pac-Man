"""The same seed must replay the same game, maze and moves included."""

from random import Random
from typing import Callable

from src import Config, Direction, GameState, Level, Maze

from capabilities import opens_a_next_stage
from gaps import missing
from helpers import open_grid


def _walls(maze: Maze) -> list[int]:
    """Returns the wall values of a maze, row by row.

    maze -- the maze to read
    """

    return [maze.get_cell(x, y).walls
            for y in range(maze.height)
            for x in range(maze.width)
            ]


def _positions(level: Level) -> list[tuple[int, int]]:
    """Returns the player and ghost cells of a level.

    level -- the level to read
    """

    return [level.player.cell.pos] + [ghost.cell.pos
                                      for ghost in level.ghosts]


def test_the_run_random_source_only_depends_on_the_seed(
        write_config: Callable[[str], str]) -> None:
    """Two runs on one seed draw the same numbers."""

    Config.load_from_file(write_config('{"seed": 42}'))
    GameState.reset()
    first = [GameState.random.random() for _ in range(5)]
    GameState.reset()

    assert [GameState.random.random() for _ in range(5)] == first


def test_two_seeds_give_two_random_sources(
        write_config: Callable[[str], str]) -> None:
    """A different seed is a different run."""

    Config.load_from_file(write_config('{"seed": 42}'))
    GameState.reset()
    first = GameState.random.random()
    Config.load_from_file(write_config('{"seed": 1337}'))
    GameState.reset()

    assert GameState.random.random() != first
    assert first == Random(42).random()


def test_spawns_are_stable_for_one_grid() -> None:
    """Two mazes built from one grid place the ghosts the same way."""

    grid = open_grid(11, 9)
    first = [cell.pos for cell in Maze(grid).spawns]

    assert [cell.pos for cell in Maze(grid).spawns] == first


def test_two_levels_on_one_grid_start_the_same() -> None:
    """Player spawn, ghost spawns and pacgums do not drift."""

    grid = open_grid(11, 9)
    first = Level(Maze(grid))
    second = Level(Maze(grid))

    assert _positions(first) == _positions(second)
    assert {gum.cell.pos for gum in first.pacgums} == {
        gum.cell.pos for gum in second.pacgums}


def test_ghosts_move_the_same_way_twice(
        write_config: Callable[[str], str]) -> None:
    """Chasing is reproducible, so a bug can be replayed."""

    Config.load_from_file(write_config('{"seed": 42}'))
    runs = []
    for _ in range(2):
        GameState.reset()
        level = Level(Maze(open_grid(15, 15)))
        GameState.level = level
        level.player.cell = level.maze.get_cell(7, 7)
        steps = []
        for _ in range(12):
            for ghost in level.ghosts:
                ghost.tick()
            steps.append(_positions(level))
        runs.append(steps)

    assert runs[0] == runs[1]


def test_the_first_maze_only_depends_on_the_seed(
        write_config: Callable[[str], str]) -> None:
    """Two runs on one seed open on the same maze."""

    Config.load_from_file(write_config('{"seed": 42}'))
    GameState.reset()
    first = _walls(GameState.level.maze)
    GameState.reset()

    assert _walls(GameState.level.maze) == first


@missing("a next stage to play", when=not opens_a_next_stage(),
         raises=AttributeError)
def test_the_later_stages_are_reproducible(
        write_config: Callable[[str], str]) -> None:
    """Stage two is random-looking but replays identically."""

    Config.load_from_file(write_config('{"seed": 42}'))
    GameState.reset()
    GameState.next_stage()
    second = _walls(GameState.level.maze)
    GameState.reset()
    GameState.next_stage()

    assert _walls(GameState.level.maze) == second


def test_a_whole_run_replays_identically(
        write_config: Callable[[str], str]) -> None:
    """Same seed, same inputs, same score and same lives."""

    Config.load_from_file(write_config('{"seed": 7, "level_time": 500}'))
    results = []
    for _ in range(2):
        GameState.reset()
        level = GameState.level
        level.player.set_direction(Direction.DOWN)
        for _ in range(15):
            level.tick()
        results.append((GameState.score, GameState.lives,
                        _positions(level), level.state))

    assert results[0] == results[1]
