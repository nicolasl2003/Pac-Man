from . import Cell, MovingEntity, RenderedEntity


class Player(MovingEntity, RenderedEntity):
    """The PacMan controlled by the player."""

    def __init__(self, spawn: Cell) -> None:
        """Creates the player.

        spawn -- The cell on which to spawn the player
        """
        super().__init__(spawn)

    def tick(self) -> None:
        raise NotImplementedError  # TODO

    def update(self, delta_time: int) -> None:
        """Updates the visual of the player.

        delta_time -- The time elapsed inbetween two frames
        """

        self.rotation = self.rotation.next(self.direction)
        super().update(delta_time)
