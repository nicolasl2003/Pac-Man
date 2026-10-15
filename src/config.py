import json
import sys
from enum import Enum
from typing import Self, Any

from pydantic import BaseModel, Field


class ConfigError(Exception):
    """Config errors Exception class."""
    pass


class ConfigWrapper:
    """The configuration of PacMan.

    framerate -- The target frames per seconds
    ticks_per_sec -- The number of ticks per seconds
    highscore_filename -- The path of the highscore data file
    name_length -- The longest name the highscores keep
    screen_width -- The width of the game window
    screen_height -- The height of the game window
    lives -- The number of lives the player has
    pacgum_count -- The number of pacgum per level, -1 for every free cell
    super_pacgum_count -- The number of super pacgum per level
    pacgum_points -- The number of points a pacgum awards
    ss_pacgum_points -- The number of points a super pacgum awards
    ghost_points -- The number of points killing a ghost gives
    seed -- The forced seed of the level
    level_time -- The seconds you get to complete de level
    ghost_count -- The number of ghosts per level
    ghost_cooldown -- How many seconds an eaten ghost waits to respawn
    ghost_edible_cooldown -- How many seconds a ghost stays frightened
    ghost_chase -- How hard the ghosts chase the player
    """

    class ConfigModel(BaseModel):
        """The data configuration of PacMan.

        framerate -- The target frames per seconds
        ticks_per_sec -- The number of ticks per seconds
        highscore_filename -- The path of the highscore data file
        name_length -- The longest name the highscores keep
        screen_width -- The width of the game window
        screen_height -- The height of the game window
        lives -- The number of lives the player has
        pacgum_count -- The number of pacgum per level, -1 for every free cell
        super_pacgum_count -- The number of super pacgum per level
        pacgum_points -- The number of points a pacgum awards
        ss_pacgum_points -- The number of points a super pacgum awards
        ghost_points -- The number of points killing a ghost gives
        seed -- The forced seed of the level
        level_time -- The seconds you get to complete de level
        ghost_count -- The number of ghosts per level
        ghost_cooldown -- How many seconds an eaten ghost waits to respawn
        ghost_edible_cooldown -- How many seconds a ghost stays frightened
        ghost_chase -- How hard the ghosts chase the player
        """

        class GhostSpawnType(Enum):
            """The cells where the ghosts spawn.

            CORNERS -- The four corners of the maze
            CLOSED_CELL -- The cells walled on all four sides
            """

            CORNERS = "corners"
            CLOSED_CELL = "closed_cell"

        class GhostChaseType(Enum):
            """The ghost chase difficulty.

            RANDOM -- The ghosts wander randomly
            NORMAL -- The ghosts aim for the player three moves ahead
            HARDCORE -- The ghosts follow the shortest path to the player
            """

            RANDOM = "Random"
            NORMAL = "Normal"
            HARDCORE = "Hardcore"

        framerate: int = Field(default=60, ge=1)
        ticks_per_sec: int = Field(default=4, ge=1)
        highscore_filename: str = Field(default="highscores.json")
        name_length: int = Field(default=10, ge=1)
        screen_width: int = Field(default=700, ge=1)
        screen_height: int = Field(default=750, ge=1)
        lives: int = Field(default=3, ge=1)
        pacgum_count: int = Field(default=-1, ge=-1)
        super_pacgum_count: int = Field(default=4, ge=0)
        pacgum_points: int = Field(default=1)
        ss_pacgum_points: int = Field(default=15)
        ghost_points: int = Field(default=20)
        seed: int = Field(default=42)
        level_time: int = Field(default=90, ge=1)
        ghost_count: int = Field(default=4, ge=0)
        ghost_spawn: GhostSpawnType = Field(default=GhostSpawnType.CORNERS)
        ghost_cooldown: int = Field(default=5)
        ghost_edible_cooldown: int = Field(default=7)
        ghost_chase: GhostChaseType = Field(default=GhostChaseType.NORMAL)

        def _dump_to_file(self, path: str) -> Self:
            try:
                with open(path, "w") as file:
                    json.dump(self.model_dump(mode="json"), file, indent=4)
            except (IOError, UnicodeEncodeError) as e:
                print(f"Could not write template config to {path}: {e}",
                      file=sys.stderr)
            except Exception as e:
                print("Could not format the config class to json:",
                      f"{type(e).__name__}: {e}",
                      file=sys.stderr)
            return self

        @classmethod
        def load_from_file(cls, path: str) -> Self:
            """Loads and parses the config file into Config.

            path -- The config file path
            """

            try:
                with open(path) as file:
                    text: str = file.read()
                # Emptied rather than removed to keep the error line numbers
                content: str = "\n".join(
                    "" if line.lstrip().startswith("#") else line
                    for line in text.splitlines())
                if text.strip() and not content.strip():
                    return cls()
                return cls(**json.loads(content))
            except FileNotFoundError:
                return cls()._dump_to_file(path)
            except (IOError, json.JSONDecodeError,
                    UnicodeDecodeError) as e:
                raise ConfigError(f"Could not load the config file: {e}"
                                  ) from None
            except (ValueError, TypeError) as e:
                raise ConfigError("Mistyped json argument"
                                  f" - Unsupported type or value {e}"
                                  ) from None

    GhostSpawnType = ConfigModel.GhostSpawnType
    GhostChaseType = ConfigModel.GhostChaseType

    framerate: int
    ticks_per_sec: int
    highscore_filename: str
    name_length: int
    screen_width: int
    screen_height: int
    lives: int
    pacgum_count: int
    super_pacgum_count: int
    pacgum_points: int
    ss_pacgum_points: int
    ghost_points: int
    seed: int
    level_time: int
    ghost_count: int
    ghost_spawn: ConfigModel.GhostSpawnType
    ghost_cooldown: int
    ghost_edible_cooldown: int
    ghost_chase: ConfigModel.GhostChaseType

    _instance: ConfigModel

    def __init__(self) -> None:
        self._instance = ConfigWrapper.ConfigModel()

    def load_from_file(self, path: str) -> None:
        """Loads and parses the config file into Config.

        path -- The config file path
        """
        self._instance = ConfigWrapper.ConfigModel.load_from_file(path)

    @property
    def ms_per_tick(self) -> int:
        """The time it takes for the game to tick."""
        return 1000 // self.ticks_per_sec

    def __getattr__(self, name: str) -> Any:
        return getattr(self._instance, name)


Config: ConfigWrapper = ConfigWrapper()
