from . import Ghost, Player, Maze


class Level:

    timer: int
    ghosts: list[Ghost]
    player: Player
    maze: Maze
