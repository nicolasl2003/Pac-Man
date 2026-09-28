from pydantic import BaseModel


class Config(BaseModel):

    highscore_filename: str
    width: int
    height: int
    lives: int
    pacgum: int
    super_pacgum: int
    pacgum_points: int
    ss_pacgum_points: int
    ghost_points: int
    seed: int
    level_timer: int
    ghost_count: int
