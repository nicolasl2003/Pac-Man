import json
import sys
from enum import Enum
from time import monotonic_ns
from typing import Self, Any

from pydantic import BaseModel, Field


class ConfigError(Exception):
    """Config errors Exception class."""
    pass


class ConfigWrapper:
    """The configuration of PacMan.

    framerate -- The target frames per seconds
    frame_per_tick -- How many in game frames to step simulation
    highscore_filename -- The path of the highscore data file
    screen_width -- The width of the game window
    screen_height -- The height of the game window
    lives -- The number of lives the player has
    pacgum_count -- The number of pacgum per level
    super_pacgum_count -- The number of super pacgum per level
    pacgum_points -- The number of points a pacgum awards
    ss_pacgum_points -- The number of points a super pacgum awards
    ghost_points -- The number of points killing a ghost gives
    seed -- The forced seed of the level
    level_time -- The time you get to complete de level
    ghost_count -- The number of ghosts per level
    ghost_cooldown -- How long in milliseconds before a ghost respawns
    ghost_edible_cooldown -- How long a ghost stays frightened
    ghost_chase -- How hard the ghosts chase the player
    """

    class ConfigModel(BaseModel):
        """The data configuration of PacMan.

        framerate -- The target frames per seconds
        frame_per_tick -- How many in game frames to step simulation
        highscore_filename -- The path of the highscore data file
        screen_width -- The width of the game window
        screen_height -- The height of the game window
        lives -- The number of lives the player has
        pacgum_count -- The number of pacgum per level
        super_pacgum_count -- The number of super pacgum per level
        pacgum_points -- The number of points a pacgum awards
        ss_pacgum_points -- The number of points a super pacgum awards
        ghost_points -- The number of points killing a ghost gives
        seed -- The forced seed of the level
        level_time -- The time you get to complete de level
        ghost_count -- The number of ghosts per level
        ghost_cooldown -- How long in milliseconds before a ghost respawns
        ghost_edible_cooldown -- How long a ghost stays frightened
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
        frame_per_tick: int = Field(default=15, ge=1)
        highscore_filename: str = Field(default="highscores.json")
        screen_width: int = Field(default=700, ge=1)
        screen_height: int = Field(default=420, ge=1)
        lives: int = Field(default=3, ge=1)
        pacgum_count: int = Field(default=40, ge=0)
        super_pacgum_count: int = Field(default=4, ge=0)
        pacgum_points: int = Field(default=1)
        ss_pacgum_points: int = Field(default=15)
        ghost_points: int = Field(default=20)
        seed: int = Field(default=monotonic_ns())
        level_time: int = Field(default=15, ge=1)
        ghost_count: int = Field(default=4, ge=0)
        ghost_spawn: GhostSpawnType = Field(default=GhostSpawnType.CORNERS)
        ghost_cooldown: int = Field(default=2)
        ghost_edible_cooldown: int = Field(default=2)
        ghost_chase: GhostChaseType = Field(default=GhostChaseType.NORMAL)

        def _dump_to_file(self, path: str) -> Self:
            try:
                with open(path, "w") as file:
                    json.dump(self.model_dump(), file, indent=4)
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
                    return cls(**json.load(file))
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
    frame_per_tick: int
    highscore_filename: str
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

    def __getattr__(self, name: str) -> Any:
        return getattr(self._instance, name)


Config: ConfigWrapper = ConfigWrapper()
