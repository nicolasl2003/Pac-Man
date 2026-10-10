from enum import Enum, auto
from . import Ghost, Player, Maze, Config


class Level:

    class State(Enum):
        """The level state.

        RUNNING -- The game is still running
        WON -- The level was won by the player
        LOST -- The player died
        """

        RUNNING = auto()
        WON = auto()
        LOST = auto()

    timer: int
    ghosts: list[Ghost]
    player: Player
    maze: Maze
    state: State

    def __init__(self, maze: Maze) -> None:
        """Creates a new level.

        maze -- The maze map to assign to the level
        """

        def _create_ghosts(ghost_count: int) -> None:
            """Creates the level ghosts."""

            self.ghosts = [Ghost(maze.get_spawn(i))
                           for i in range(ghost_count)
                           ]

        self.timer = 0
        self.maze = maze
        self.player = Player(maze.get_cell((0, 0)))
        _create_ghosts(Config.ghost_count)
        self.state = Level.State.RUNNING

    def lost(self) -> None:
        self.state = Level.State.LOST
        raise NotImplementedError  # TODO

    def tick(self) -> State:
        """Ticks all the level members."""

        self.player.tick()
        for ghost in self.ghosts:
            ghost.tick()
        return self.state

    def update(self, delta_time: int) -> None:
        """Updates the graphic aspect of the level.

        delta_time -- The time spent since last frame
        """
        # TODO: draw level
        self.maze.update(delta_time)
        for ghost in self.ghosts:
            ghost.update(delta_time)
