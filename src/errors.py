from . import Cell, MovingEntity


class CellNotFoundError(Exception):
    """Error when a cell is not part of the maze."""

    def __init__(self, first: tuple[int, int] | str) -> None:
        """Creates the error.

        first -- The coordinates or name of the cell
        """

        if isinstance(first, tuple):
            super().__init__(f"Cell at {first} is not part of the maze")
        else:
            super().__init__(f"Cell {first} not found")


class EntityBlockedError(Exception):
    """Error when the entity cannot move to the designated cell."""

    def __init__(self, entity: MovingEntity, cell: Cell) -> None:
        """Creates the error.

        entity -- The entity that got blocked in its move
        cell -- The cell it tried to reach
        """

        super().__init__(f"Entity {type(entity).__name__}"
                         f" cannot reach cell {cell}")
