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


class AssetError(Exception):
    """Error when an image or a sound the game needs cannot be loaded."""

    def __init__(self, what: str, cause: Exception) -> None:
        """Creates the error.

        what -- What the game was loading, such as "the game sprites"
        cause -- The error raised while loading the file, naming it
        """

        super().__init__(f"[Assets] {what} : {cause}")
