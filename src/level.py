from . import Ghost, Player, Maze
from enum import Enum, auto()


class Level:

    timer: int
    ghosts: list[Ghost]
    player: Player
    maze: Maze
    state: State

    class State(Enum):
        """The level state.

        RUNNING -- The game is still running
        WON -- The level was won by the player
        LOST -- The player died
        """

        RUNNING = auto()
        WON = auto()
        LOST = auto()

    def __init__(self, maze: Maze) -> None:
        """Creates a new level.

        maze -- The maze map to assign to the level
        """

        def _create_ghosts(ghost_count: int) -> None:
            """Creates the level ghosts."""

            self.ghosts = [Ghost(maze.get_spawn(ghost_count))
                           for i in range(ghost_count)
                           ]

        self.timer = 0
        _create_ghosts(Config.ghost_count)


    def lost(self) -> None:
        raise NotImplementedError  # TODO

    def tick(self) -> Level.State:
        """Ticks all the level members."""

        player.tick()
        for ghost in ghosts:
            ghost.tick()
        return state

    def update(self, delta_time: int) -> None:
        """Updates the graphic aspect of the level.

        delta_time -- The time spent since last frame
        """

        # TODO: draw level
        for ghost in ghosts:
            ghost.update(delta_time)
        player.update(delta_time)
