from enum import Enum, auto
from heapq import heappop, heappush
from typing import Any

from . import CellNotFoundError, Cell, Maze, Direction, Config, GameState


class Entity:
    """A generic entity class that stores common code for entities.

    stored -- The container the entity in stored in
    spawn -- The cell used on respawn
    cell -- The cell the entity stands on
    """

    stored: list[Any]
    spawn: Cell
    cell: Cell

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "cell" and isinstance(value, Cell):
            try:
                self.cell.entities.remove(self)
            except (ValueError, AttributeError):
                pass
        super().__setattr__(name, value)
        if name == "cell" and self not in self.cell.entities:
            self.cell.entities.append(self)

    def __init__(self, spawn: Cell) -> None:
        """Creates the entity.

        spawn -- The spawn cell of the entity
        """
        self.spawn = spawn
        self.respawn()

    def respawn(self) -> None:
        """Put the entity back on its spawn cell."""

        self.cell = self.spawn


class Rotation(Enum):
    """The rotation angle of the visuals of the entity.

        UP -- The up rotation
        RIGHT -- The right rotation
        DOWN -- The down rotation
        LEFT -- The left rotation
    """

    UP = NotImplemented
    RIGHT = NotImplemented
    DOWN = NotImplemented
    LEFT = NotImplemented

    def next(self, direction: Direction) -> Any:
        """Retrieves the rotation to have on a direction change.

        direction -- The direction to use to determine the rotation
        """

        try:
            return self.from_direction(direction)
        except KeyError:
            return self

    @classmethod
    def from_direction(cls, direction: Direction) -> Any:
        """Transforms a direction into a rotation.

        direction -- The direction to use to determine the rotation

        Raises KeyError if the direction has no corresponding rotation
        """
        return DirectionToRotation[direction]


DirectionToRotation: dict[Direction, Rotation] = {
    Direction.UP: Rotation.UP,
    Direction.RIGHT: Rotation.RIGHT,
    Direction.DOWN: Rotation.DOWN,
    Direction.LEFT: Rotation.LEFT
}


class RenderedEntity(Entity):
    """A generic entity class that stores common code for rendering.

    x -- The x position of the entity on screen
    y -- The y position of the entity on screen
    rotation -- The rotation angle of the visuals of the entity
    """

    x: int
    y: int
    shown: bool
    rotation: Rotation
    image: Any  # TODO

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "cell" and isinstance(value, Cell):
            self.x = value.x
            self.y = value.y
        super().__setattr__(name, value)

    def respawn(self) -> None:
        super().respawn()
        self.shown = True
        self.x = self.cell.x
        self.y = self.cell.y
        self.rotation = Rotation.RIGHT
        self.image = NotImplemented  # TODO

    def update(self, delta_time: int) -> None:
        """Updates the visual of the entity.

        delta_time -- The time elapsed inbetween two frames
        """

        raise NotImplementedError  # TODO


class NotEdibleError(Exception):
    """Error when an entity cannot be eaten."""

    def __init__(self, entity: Entity):
        """Creates the error.

        entity -- The entity you tried to eat
        """

        super().__init__(f"Cannot eat the entity {entity}")


class EdibleEntity(RenderedEntity):
    """A generic entity class that can be eaten by the player.

    edible -- Whether the entity can be eaten or not
    prize --  The amount of points given to the player if eaten
    """

    edible: bool
    prize: int

    def __init__(self, spawn: Cell, points: int):
        """Creates the entity.

        spawn -- The cell on which the entity appears
        points -- The prize given to the player when eaten
        """

        # Set first: Ghost.respawn, run by Entity.__init__, calms the ghost
        self.edible = True
        super().__init__(spawn)
        self.prize = points

    def eat(self) -> int:
        """Eats the entity to oblivion.

        Raises NotEdibleError if the entity is not eatable
        """

        if not self.edible:
            raise NotEdibleError(self)

        self.stored.remove(self)
        self.cell.entities.remove(self)
        return self.prize


class MovingEntity(RenderedEntity):
    """A generic entity class that stores common code for moving entities.

    direction -- The current direction
    can_collide -- Can the entity collide with another
    """

    direction: Direction
    can_collide: bool

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name == "direction" and isinstance(value, Direction):
            self.update_rotation()

    def update_rotation(self) -> None:
        """Updates the entity rotation accordingly to the direction."""

        self.rotation = self.rotation.next(self.direction)

    def respawn(self) -> None:
        """Put the entity back on its spawn cell."""

        super().respawn()
        self.direction = Direction.STILL
        self.can_collide = True

    def can_move(self, cell: Cell, direction: Direction) -> bool:
        """Returns whether the entity can leave a cell toward a direction.

        cell -- The cell the entity would leave
        direction -- The direction it would take
        """

        return cell.can_move(direction)

    def move(self, direction: Direction) -> None:
        """Moves one cell towards a direction.

        direction -- The direction you move the entity
        """

        self.direction = direction

        if self.direction == Direction.STILL:
            return

        if not self.can_move(self.cell, self.direction):
            return

        from src import GameState

        maze: Maze = GameState.level.maze
        try:
            self.cell = maze.get_neighbor(self.cell, self.direction)
        except CellNotFoundError:
            return

    def collides(self, other: Entity) -> bool:
        """Return whether both entities collide on a cell."""

        if not self.can_collide:
            return False

        if isinstance(other, MovingEntity) and not other.can_collide:
            return False

        if not isinstance(other, Entity):
            return False

        return True if self.cell == other.cell else False


class PacGum(EdibleEntity):
    """Pacgum class that is edible."""

    def __init__(self, spawn: Cell) -> None:
        """Creates the pacgum.

        spawn -- The cell on which the entity appears
        """

        super().__init__(spawn, Config.pacgum_points)


class SuperPacGum(EdibleEntity):
    """Super Pacgum class that is edible."""

    def __init__(self, spawn: Cell) -> None:
        """Creates the super pacgum.

        spawn -- The cell on which the entity appears
        """

        super().__init__(spawn, Config.ss_pacgum_points)

    def eat(self) -> int:
        """Eats the entity to oblivion.

        Raises NotEdibleError if the entity is not eatable
        """

        if not super().eat():
            return False

        for ghost in GameState.level.ghosts:
            ghost.frighten()

        return True


class Ghost(MovingEntity, EdibleEntity):
    """Ghost class of the game.

    mode -- The current behavior of the ghost
    respawn_cooldown -- The amount of time left before the ghost respawns
    edible_cooldown -- The cooldown for which the ghost is edible
    planned_path -- The cells the ghost crosses before planning again
    """

    class GhostMode(Enum):
        """The ghost behaviors.

        CHASE -- Chase mode
        EDIBLE -- Edible mode
        """

        CHASE = auto()
        EDIBLE = auto()
        DEAD = auto()

    mode: GhostMode
    respawn_cooldown: int
    edible_cooldown: int
    planned_path: list[Cell]

    _LOCKED_ROTATIONS = [Rotation.RIGHT, Rotation.LEFT]

    def __init__(self, spawn: Cell) -> None:
        """Creates the ghost.

        spawn -- The cell on which to spawn the ghost
        """

        super().__init__(spawn, Config.ghost_points)

    def __setattr__(self, name: str, value: Any) -> None:
        """Resets the planned path whenever the mode changes."""

        super().__setattr__(name, value)
        if name == "mode":
            self.planned_path = []

    def update_rotation(self) -> None:
        """Updates the entity rotation accordingly to the direction."""

        if self.rotation.next(self.direction) in self._LOCKED_ROTATIONS:
            self.rotation = self.rotation.next(self.direction)

    def respawn(self) -> None:
        """Puts the entity back on its spawn cell."""

        super().respawn()
        self.shown = True
        self.respawn_cooldown = 0
        self.calm()

    def can_move(self, cell: Cell, direction: Direction) -> bool:
        """Returns whether the ghost can leave a cell toward a direction.

        A ghost on a closed cell ignores its walls, so it can leave the '42'.
        cell -- The cell the ghost would leave
        direction -- The direction it would take
        """

        return not cell.accessible or super().can_move(cell, direction)

    def tick(self) -> None:
        """Steps the ghost logic by one."""

        from src import GameState

        def _neighbors(cell: Cell) -> list[Cell]:
            """Returns the cells the ghost can reach from a cell in one move.

            cell -- The cell departed from
            """

            maze: Maze = GameState.level.maze
            return [maze.get_neighbor(cell, direction)
                    for direction in Direction
                    if direction != Direction.STILL
                    and self.can_move(cell, direction)]

        def _distance(position: tuple[int, int],
                      target: tuple[int, int]) -> int:
            """Returns the number of moves between two positions without walls.

            position -- The position departed from
            target -- The position to reach
            """

            return abs(position[0] - target[0]) + abs(position[1] - target[1])

        def _direction_to(step: Cell) -> Direction:
            """Returns the direction from the ghost cell to a neighbor cell.

            step -- The neighbor cell to reach
            """

            maze: Maze = GameState.level.maze
            # A tunnel step crosses the grid, so the coordinates cannot tell
            return next(direction for direction in Direction
                        if maze.get_neighbor(self.cell, direction) == step)

        def _path_to(parents: dict[Cell, Cell], end: Cell) -> list[Cell]:
            """Returns the cells to cross from the ghost cell to a found cell.

            parents -- The cell from which each found cell was reached
            end -- The last cell of the path
            """

            path: list[Cell] = []
            current: Cell = end
            while current != self.cell:
                path.append(current)
                current = parents[current]
            path.reverse()
            return path

        def _plan_three_moves(target: tuple[int, int]) -> list[Cell]:
            """Returns the three-cell path that ends closest to a target.

            target -- The position to get close to, possibly outside the maze
            """

            parents: dict[Cell, Cell] = {}
            frontier: list[Cell] = [self.cell]
            for depth in range(3):
                next_frontier: list[Cell] = []
                for current in frontier:
                    for neighbor in _neighbors(current):
                        if neighbor == self.cell or neighbor in parents:
                            continue
                        parents[neighbor] = current
                        next_frontier.append(neighbor)
                if not next_frontier:
                    break
                frontier = next_frontier
            closest: Cell = min(frontier,
                                key=lambda cell: _distance(cell.pos, target))
            return _path_to(parents, closest)

        def _move_random() -> None:
            """Moves the ghost toward a random direction."""

            self.move(GameState.random.sample(list(Direction), 1)[0])

        def _move_normal(target: tuple[int, int]) -> None:
            """Moves the ghost along its planned path toward a target.

            target -- The position to get close to when a new path is planned
            """

            if not self.planned_path:
                self.planned_path = _plan_three_moves(target)
            if self.planned_path:
                self.move(_direction_to(self.planned_path.pop(0)))

        def _move_hardcore() -> None:
            """Moves the ghost along the shortest path to the player."""

            target: Cell = GameState.level.player.cell
            parents: dict[Cell, Cell] = {}
            costs: dict[Cell, int] = {self.cell: 0}
            queue: list[tuple[int, int, Cell]] = [
                (_distance(self.cell.pos, target.pos), 0, self.cell)]
            loop_count: int = 0
            while queue:
                current: Cell = heappop(queue)[2]
                if current == target:
                    path: list[Cell] = _path_to(parents, current)
                    if path:
                        self.move(_direction_to(path[0]))
                    return
                for neighbor in _neighbors(current):
                    cost: int = costs[current] + 1
                    if neighbor in costs and costs[neighbor] <= cost:
                        continue
                    costs[neighbor] = cost
                    parents[neighbor] = current
                    loop_count += 1
                    heappush(queue, (cost + _distance(neighbor.pos,
                                                      target.pos),
                                     loop_count, neighbor))

        def _chase() -> None:
            """Moves the ghost following the configured chase difficulty."""

            match Config.ghost_chase:
                case Config.GhostChaseType.RANDOM:
                    _move_random()
                case Config.GhostChaseType.NORMAL:
                    _move_normal(GameState.level.player.cell.pos)
                case Config.GhostChaseType.HARDCORE:
                    _move_hardcore()

        def _flee() -> None:
            """Moves the ghost toward the opposite side of the player."""

            player: Cell = GameState.level.player.cell
            _move_normal((2 * self.cell.x - player.x,
                          2 * self.cell.y - player.y))

        match self.mode:
            case self.GhostMode.CHASE:
                _chase()
            case self.GhostMode.EDIBLE:
                if self.edible_cooldown == 0:
                    self.calm()
                    return
                self.edible_cooldown -= 1
                _flee()
            case self.GhostMode.DEAD:
                if self.respawn_cooldown == 0:
                    self.respawn()
                    return
                self.respawn_cooldown -= 1

    def frighten(self) -> None:
        """Makes the ghost edible for some time."""

        self.mode = self.GhostMode.EDIBLE
        self.edible_cooldown = Config.to_ticks(Config.ghost_edible_cooldown)
        self.edible = True

    def calm(self) -> None:
        """Puts the ghost back into chase mode."""

        self.edible = False
        self.mode = self.GhostMode.CHASE

    def eat(self) -> int:
        """Remove the ghost from the level until he respawns."""

        if not self.edible:
            raise NotEdibleError(self)

        self.mode = self.GhostMode.DEAD
        self.edible = False
        self.cell = Cell(-1, -1, 15)
        self.respawn_cooldown = Config.to_ticks(Config.ghost_cooldown)
        return self.prize
