"""Ghost chase difficulties (Random, Normal, Hardcore) and the edible flee.

The ghosts are placed by hand on grids built from wall bits. The expected moves
are re-derived from those bits, without going through Maze or the ghost code.
"""

import random
from collections import deque
from typing import Callable, Iterator

import pytest
from mazegenerator import MazeGenerator

from src import Cell, Config, Direction, GameState, Ghost, Maze, Player
from src.config import ConfigError

from capabilities import clamps_a_bad_config_value
from gaps import missing

from helpers import close_passage, manhattan, open_grid, seal_cell

_BITS: dict[tuple[int, int], int] = {(0, -1): 1, (1, 0): 2,
                                     (0, 1): 4, (-1, 0): 8}


def _open_moves(grid: list[list[int]],
                pos: tuple[int, int]) -> Iterator[tuple[int, int]]:
    """Yields the positions reachable in one move, read from the wall bits.

    grid -- the grid, indexed as grid[y][x]
    pos -- the position departed from
    """

    for (step_x, step_y), bit in _BITS.items():
        next_x, next_y = pos[0] + step_x, pos[1] + step_y
        if (grid[pos[1]][pos[0]] & bit == 0
                and 0 <= next_x < len(grid[0]) and 0 <= next_y < len(grid)):
            yield (next_x, next_y)


def _distances(grid: list[list[int]],
               origin: tuple[int, int]) -> dict[tuple[int, int], int]:
    """Returns the number of moves from origin to every reachable position.

    grid -- the grid, indexed as grid[y][x]
    origin -- the position departed from
    """

    distances: dict[tuple[int, int], int] = {origin: 0}
    queue: deque[tuple[int, int]] = deque([origin])
    while queue:
        current = queue.popleft()
        for reached in _open_moves(grid, current):
            if reached not in distances:
                distances[reached] = distances[current] + 1
                queue.append(reached)
    return distances


def _manhattan(first: tuple[int, int], second: tuple[int, int]) -> int:
    """Returns the distance between two positions, walls ignored.

    first -- one position
    second -- the other position
    """

    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _generated_grid() -> list[list[int]]:
    """Returns a fixed braided maze from the subject's generator."""

    return MazeGenerator(size=(15, 15), perfect=False, seed=42).maze


ChaseBuilder = Callable[[list[list[int]], tuple[int, int], tuple[int, int],
                         str], Ghost]


@pytest.fixture
def chase(write_config: Callable[[str], str]) -> ChaseBuilder:
    """Returns a helper placing a ghost and the player on a grid."""

    def _build(grid: list[list[int]], ghost_pos: tuple[int, int],
               player_pos: tuple[int, int], difficulty: str) -> Ghost:
        Config.load_from_file(
            write_config(f'{{"ghost_chase": "{difficulty}"}}'))
        maze = Maze(grid)
        GameState.level.maze = maze
        GameState.level.player = Player(maze.get_cell(player_pos))
        return Ghost(maze.get_cell(ghost_pos), 0)

    return _build


# --- Maze helpers used by the chase -----------------------------------------

def test_still_is_no_move_out_of_a_sealed_cell() -> None:
    """Direction.STILL is refused, and never raises a KeyError."""

    grid = open_grid(3, 3)
    seal_cell(grid, 1, 1)
    assert not Maze(grid).get_cell(1, 1).can_move(Direction.STILL)


def test_neighbors_skip_walled_sides() -> None:
    """A wall removes the cell behind it from the neighbors."""

    grid = open_grid(3, 3)
    close_passage(grid, 1, 1, Direction.RIGHT)
    maze = Maze(grid)
    assert {cell.pos for cell in maze.neighbors(maze.get_cell(1, 1))} == {
        (1, 0), (0, 1), (1, 2)}


def test_neighbors_never_return_the_cell_itself() -> None:
    """STILL being allowed does not make a cell its own neighbor."""

    maze = Maze(open_grid(3, 3))
    cell = maze.get_cell(1, 1)
    assert cell not in set(maze.neighbors(cell))


# --- Config ------------------------------------------------------------------

def test_default_chase_is_normal() -> None:
    """Without a ghost_chase key the ghosts play in Normal."""

    assert Config.ghost_chase == Config.GhostChaseType.NORMAL


@pytest.mark.parametrize("difficulty", ["Random", "Normal", "Hardcore"])
def test_chase_is_read_from_the_config(write_config: Callable[[str], str],
                                       difficulty: str) -> None:
    """Every difficulty name of the config is accepted."""

    Config.load_from_file(write_config(f'{{"ghost_chase": "{difficulty}"}}'))
    assert Config.ghost_chase.value == difficulty


@missing("a config that carries on with an unknown difficulty",
         when=not clamps_a_bad_config_value(), raises=ConfigError)
@pytest.mark.parametrize("difficulty", ["hardcore", "Hard", "", "1"])
def test_unknown_chase_does_not_stop_the_game(
        write_config: Callable[[str], str], difficulty: str,
        capsys: pytest.CaptureFixture[str]) -> None:
    """An unknown difficulty name is replaced, and reported."""

    Config.load_from_file(
        write_config(f'{{"ghost_chase": "{difficulty}"}}'))

    assert isinstance(Config.ghost_chase, Config.GhostChaseType)
    assert capsys.readouterr().err


# --- Random -----------------------------------------------------------------

def test_random_ghost_only_steps_through_open_sides(chase: ChaseBuilder
                                                    ) -> None:
    """A random ghost stays put or crosses an open side, tick after tick."""

    grid = _generated_grid()
    ghost = chase(grid, (0, 0), (14, 14), "Random")
    for _ in range(300):
        before = ghost.cell.pos
        ghost.tick()
        assert ghost.cell.pos == before or ghost.cell.pos in set(
            _open_moves(grid, before))


# --- Normal -----------------------------------------------------------------

def _three_move_ends(grid: list[list[int]], start: tuple[int, int],
                     target: tuple[int, int]) -> set[tuple[int, int]]:
    """Returns the cells three moves away that end closest to a target.

    A start with no cell three moves away falls back on its deepest cells.
    grid -- the grid, indexed as grid[y][x]
    start -- the ghost position
    target -- the position to get close to, possibly outside the grid
    """

    from_start = _distances(grid, start)
    depth = min(3, max(from_start.values()))
    ends = [pos for pos, distance in from_start.items() if distance == depth]
    best = min(_manhattan(pos, target) for pos in ends)
    return {pos for pos in ends if _manhattan(pos, target) == best}


def _walk_three_ticks(ghost: Ghost, grid: list[list[int]],
                      start: tuple[int, int]) -> tuple[int, int]:
    """Ticks a ghost three times, checking each tick goes one move further.

    ghost -- the ghost to tick
    grid -- the grid, indexed as grid[y][x]
    start -- the ghost position before the first tick
    """

    from_start = _distances(grid, start)
    depth = min(3, max(from_start.values()))
    for step in range(1, depth + 1):
        ghost.tick()
        assert from_start[ghost.cell.pos] == step
    return ghost.cell.pos


def test_normal_walks_three_cells_toward_the_player(chase: ChaseBuilder
                                                    ) -> None:
    """On a generated maze, three ticks end on the best cell three moves away.

    The best cell is the one closest to the player, walls ignored.
    """

    grid = _generated_grid()
    open_cells = [(x, y) for y in range(15) for x in range(15)
                  if grid[y][x] != 15]
    for ghost_pos in open_cells[::7]:
        for player_pos in open_cells[3::11]:
            ghost = chase(grid, ghost_pos, player_pos, "Normal")
            end = _walk_three_ticks(ghost, grid, ghost_pos)
            assert end in _three_move_ends(grid, ghost_pos, player_pos)
            assert ghost.planned_path == []


def test_normal_does_not_stop_on_a_close_player(chase: ChaseBuilder) -> None:
    """A player two moves away does not shorten the three-cell walk."""

    grid = open_grid(9, 9)
    ghost = chase(grid, (4, 4), (4, 6), "Normal")
    end = _walk_three_ticks(ghost, grid, (4, 4))
    assert _manhattan(end, (4, 4)) == 3
    assert end in _three_move_ends(grid, (4, 4), (4, 6))


def test_normal_keeps_its_path_when_the_player_moves(chase: ChaseBuilder
                                                     ) -> None:
    """The three-cell path is walked to its end before a new one is planned."""

    grid = open_grid(9, 9)
    ghost = chase(grid, (4, 4), (4, 8), "Normal")
    ghost.tick()
    GameState.level.player.cell = GameState.level.maze.get_cell(4, 0)
    ghost.tick()
    ghost.tick()
    assert ghost.cell.pos == (4, 7)
    ghost.tick()
    assert ghost.cell.pos == (4, 6)


def test_mode_change_forgets_the_path(chase: ChaseBuilder) -> None:
    """Becoming edible or calming down drops the rest of the planned path."""

    ghost = chase(open_grid(9, 9), (4, 4), (4, 8), "Normal")
    ghost.tick()
    assert len(ghost.planned_path) == 2
    ghost.frighten()
    assert ghost.planned_path == []
    ghost.tick()
    assert ghost.planned_path != []
    ghost.calm()
    assert ghost.planned_path == []


@pytest.mark.parametrize("difficulty", ["Random", "Normal", "Hardcore"])
def test_a_ghost_walks_out_of_a_sealed_cell(chase: ChaseBuilder,
                                            difficulty: str) -> None:
    """A ghost spawned in the '42' pattern ignores its walls to leave it."""

    grid = open_grid(5, 5)
    seal_cell(grid, 2, 2)
    ghost = chase(grid, (2, 2), (0, 0), difficulty)
    for _ in range(20):
        ghost.tick()
        if ghost.cell.pos != (2, 2):
            break
    assert ghost.cell.pos != (2, 2)


def test_a_ghost_never_walks_into_a_sealed_cell(chase: ChaseBuilder
                                                ) -> None:
    """Walls still hold from outside: the chase goes around the cell."""

    grid = open_grid(5, 5)
    seal_cell(grid, 2, 2)
    ghost = chase(grid, (2, 1), (2, 3), "Hardcore")
    visited: set[tuple[int, int]] = set()
    for _ in range(6):
        ghost.tick()
        visited.add(ghost.cell.pos)
    assert (2, 2) not in visited
    assert (2, 3) in visited


# --- Flee -------------------------------------------------------------------

def _frighten_for_long(ghost: Ghost) -> None:
    """Makes a ghost edible for more ticks than a test walks.

    ghost -- the ghost to frighten
    """

    ghost.frighten()
    ghost.edible_cooldown = 10


@pytest.mark.parametrize("difficulty", ["Random", "Normal", "Hardcore"])
def test_edible_ghost_runs_away_from_the_player(chase: ChaseBuilder,
                                                difficulty: str) -> None:
    """Whatever the difficulty, an edible ghost walks three cells away."""

    grid = open_grid(9, 9)
    ghost = chase(grid, (4, 4), (4, 6), difficulty)
    _frighten_for_long(ghost)
    end = _walk_three_ticks(ghost, grid, (4, 4))
    assert end in _three_move_ends(grid, (4, 4), (4, 2))
    assert _manhattan(end, (4, 6)) == 5


def test_edible_ghost_flees_toward_the_opposite_of_the_player(
        chase: ChaseBuilder) -> None:
    """On a generated maze, the ghost flees toward the mirrored player.

    The player is mirrored around the ghost, possibly outside the maze.
    """

    grid = _generated_grid()
    open_cells = [(x, y) for y in range(15) for x in range(15)
                  if grid[y][x] != 15]
    for ghost_pos in open_cells[::7]:
        for player_pos in open_cells[3::11]:
            ghost = chase(grid, ghost_pos, player_pos, "Normal")
            _frighten_for_long(ghost)
            flee_target = (2 * ghost_pos[0] - player_pos[0],
                           2 * ghost_pos[1] - player_pos[1])
            end = _walk_three_ticks(ghost, grid, ghost_pos)
            assert end in _three_move_ends(grid, ghost_pos, flee_target)


def test_edible_ghost_calms_down_and_chases_again(chase: ChaseBuilder
                                                  ) -> None:
    """Once the edible cooldown is spent the ghost chases with a new path."""

    ghost = chase(open_grid(9, 9), (4, 4), (4, 8), "Normal")
    ghost.frighten()
    cooldown = Config.ghost_edible_cooldown * 1000 // Config.ms_per_tick
    for _ in range(cooldown + 1):
        ghost.tick()
    assert ghost.mode == Ghost.GhostMode.CHASE
    assert ghost.planned_path == []


# --- Hardcore ---------------------------------------------------------------

def test_hardcore_takes_the_detour_around_a_wall(chase: ChaseBuilder
                                                 ) -> None:
    """The ghost walks away from the player when the wall forces it to."""

    grid = open_grid(5, 3)
    close_passage(grid, 1, 0, Direction.RIGHT)
    close_passage(grid, 1, 1, Direction.RIGHT)
    ghost = chase(grid, (1, 0), (3, 0), "Hardcore")
    ghost.tick()
    assert ghost.cell.pos == (1, 1)


def test_hardcore_follows_a_shortest_path(chase: ChaseBuilder) -> None:
    """On a generated maze, each tick brings the ghost one move closer."""

    grid = _generated_grid()
    open_cells = [(x, y) for y in range(15) for x in range(15)
                  if grid[y][x] != 15]
    for ghost_pos in open_cells[::9]:
        for player_pos in open_cells[5::13]:
            to_player = _distances(grid, player_pos)
            ghost = chase(grid, ghost_pos, player_pos, "Hardcore")
            for remaining in range(to_player[ghost_pos], 0, -1):
                ghost.tick()
                assert to_player[ghost.cell.pos] == remaining - 1
            assert ghost.cell.pos == player_pos


def test_hardcore_ghost_on_the_player_stays(chase: ChaseBuilder) -> None:
    """A ghost already on the player does not walk away."""

    ghost = chase(open_grid(5, 5), (2, 2), (2, 2), "Hardcore")
    ghost.tick()
    assert ghost.cell.pos == (2, 2)


def test_hardcore_ghost_without_a_path_closes_in(
        chase: ChaseBuilder) -> None:
    """A target out of reach is still chased, up to the nearest cell."""

    grid = open_grid(5, 5)
    seal_cell(grid, 4, 4)
    ghost = chase(grid, (0, 0), (4, 4), "Hardcore")
    before = manhattan(ghost.cell.pos, (4, 4))

    ghost.tick()

    assert manhattan(ghost.cell.pos, (4, 4)) < before


# --- Determinism ------------------------------------------------------------

@pytest.mark.parametrize("difficulty", ["Random", "Normal", "Hardcore"])
def test_chase_is_deterministic(chase: ChaseBuilder, difficulty: str) -> None:
    """The same start and the same seed give the same trail."""

    def _trail() -> list[tuple[int, int]]:
        """Returns the cells crossed by a ghost during 40 ticks."""

        ghost = chase(_generated_grid(), (0, 0), (14, 14), difficulty)
        GameState.random.seed(Config.seed)
        cells: list[Cell] = []
        for _ in range(40):
            ghost.tick()
            cells.append(ghost.cell)
        return [cell.pos for cell in cells]

    assert _trail() == _trail()


def test_random_chase_only_draws_from_the_game_seed(
        chase: ChaseBuilder) -> None:
    """The random walk replays from GameState.random, and from nothing else.

    The generator seeds the global random module, so a trail built on a
    generated grid cannot tell the two sources apart: this one uses a
    hand-made grid and reseeds the global module from the system.
    """

    def _trail() -> list[tuple[int, int]]:
        """Returns the cells crossed by a random ghost during 40 ticks."""

        ghost = chase(open_grid(15, 15), (7, 7), (14, 14), "Random")
        GameState.random.seed(Config.seed)
        random.seed()
        cells: list[Cell] = []
        for _ in range(40):
            ghost.tick()
            cells.append(ghost.cell)
        return [cell.pos for cell in cells]

    assert _trail() == _trail()
