from . import Direction, Cell, Entity, MovingEntity


class Player(MovingEntity):
    """The PacMan controlled by the player."""

    def __init__(self, spawn: Cell) -> None:
        """Creates the player.

        spawn -- The cell on which to spawn the player
        """
        super().__init__(spawn)
        self.next_direction: Direction = self.direction

    def set_direction(self, direction: Direction) -> None:
        self.next_direction = direction

    def tick(self) -> None:
        if (self.next_direction == Direction.STILL):
            self.direction = Direction.STILL
            return

        if (self.cell.can_move(self.next_direction)):
            self.direction = self.next_direction
        elif (not self.cell.can_move(self.direction)):
            self.direction = Direction.STILL
            return

        self.move(self.direction)

    def get_collisions(self) -> list[Entity]:
        """Lists all the collisions of the player."""

        return [entity
                for entity in self.cell.entities
                if entity is not self and self.collides(entity)
                ]

    def move(self, direction: Direction) -> None:
        """Moves one cell towards a direction.

        direction -- The direction you move the entity
        """

        super().move(direction)

        from src import GameState, EdibleEntity, Ghost

        for collision in self.get_collisions():
            if isinstance(collision, EdibleEntity) and collision.edible:
                collision.eat()
            elif isinstance(collision, Ghost):
                GameState.level.lose_life()

    def update(self, delta_time: int) -> None:
        """Updates the visual of the player.

        delta_time -- The time elapsed inbetween two frames
        """

        super().update(delta_time)
