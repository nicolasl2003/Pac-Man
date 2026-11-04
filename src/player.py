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
        """Stores the direction the player takes on the next tick.

        direction -- The direction the player was asked to take
        """

        self.next_direction = direction

    def tick(self) -> None:
        """Moves the player one cell toward the direction it was given.
        """

        self.move(self.next_direction)

    def get_collisions(self) -> list[Entity]:
        """Lists all the collisions of the player."""

        return [entity
                for entity in self.cell.entities
                if entity is not self and self.collides(entity)
                ]

    def move(self, direction: Direction) -> None:
        """Moves one cell towards a direction.

        Checks collision before and after move to properly get rid of ghosts

        direction -- The direction you move the entity
        """

        from src import GameState, EdibleEntity, Ghost

        def _collide() -> bool:
            """Eats what the player stands on, or meets a ghost.

            Returns whether the player lost a life
            """

            for collision in self.get_collisions():
                if (isinstance(collision, EdibleEntity)
                        and (collision.edible or GameState.cheat)):
                    GameState.score += collision.eat()
                elif isinstance(collision, Ghost):
                    GameState.level.lose_life()
                    return True
            return False

        if _collide():
            return
        super().move(direction)
        _collide()
