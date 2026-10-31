"""Score and lives follow the player from one stage to the next."""

from random import Random
from typing import Callable

from src import Config, GameState, Level

from src.scores import load_scores, save_score

from capabilities import keeps_scores_as_models, opens_a_next_stage
from gaps import missing
from helpers import remove_ghosts
from review import verifies


def _clear_the_level(level: Level) -> None:
    """Eats every pacgum of a level, ghosts removed.

    level -- the level to empty
    """

    remove_ghosts(level)
    for gum in list(level.pacgums):
        level.player.cell = gum.cell
        level.tick()


@verifies("src.game_state.GameStateModel.reset")
def test_a_new_run_starts_at_the_first_stage() -> None:
    """A game opens on its first stage with a full score sheet."""

    assert GameState.stage in (0, 1)
    assert GameState.score == 0
    assert GameState.lives == Config.lives


@verifies("src.game_state.GameStateModel.reset")
def test_a_new_run_clears_the_score_and_the_stage() -> None:
    """Losing everything starts the next game from scratch."""

    GameState.score = 500
    GameState.stage = 4
    GameState.lives = 0
    GameState.reset()

    assert GameState.score == 0
    assert GameState.stage in (0, 1)
    assert GameState.lives == Config.lives


@verifies("src.game_state.GameStateModel.reset")
def test_a_new_run_opens_a_running_level() -> None:
    """A reset hands back a level ready to play."""

    GameState.reset()

    assert GameState.level.state is Level.State.RUNNING
    assert GameState.level.pacgums


@verifies("src.game_state.GameStateModel.reset")
def test_a_new_run_seeds_its_own_random_source(
        write_config: Callable[[str], str]) -> None:
    """The run carries the generator every random choice must use."""

    Config.load_from_file(write_config('{"seed": 42}'))
    GameState.reset()

    assert isinstance(GameState.random, Random)
    assert GameState.random.random() == Random(42).random()


@missing("scores kept as pydantic models",
         when=not keeps_scores_as_models(), raises=AttributeError)
@verifies("src.scores.save_score")
def test_a_finished_run_can_be_saved_to_the_leaderboard() -> None:
    """The score of a finished run is what the table receives."""

    GameState.score = 1234
    save_score("Sannaka", GameState.score)

    assert load_scores()[0].model_dump() == {"name": "Sannaka",
                                             "score": 1234}


@missing("a next stage to play", when=not opens_a_next_stage(),
         raises=AttributeError)
@verifies("src.game_state.GameStateModel.next_stage")
def test_winning_a_stage_keeps_the_score(
        write_config: Callable[[str], str]) -> None:
    """Points earned stay earned across stages."""

    Config.load_from_file(write_config('{"level_time": 500}'))
    GameState.reset()
    _clear_the_level(GameState.level)
    earned = GameState.score
    GameState.next_stage()

    assert GameState.score == earned
    assert earned > 0


@missing("a next stage to play", when=not opens_a_next_stage(),
         raises=AttributeError)
@verifies("src.game_state.GameStateModel.next_stage")
def test_winning_a_stage_keeps_the_lives(
        write_config: Callable[[str], str]) -> None:
    """A life lost on stage one is still lost on stage two."""

    Config.load_from_file(write_config('{"level_time": 500}'))
    GameState.reset()
    GameState.lives -= 1
    remaining = GameState.lives
    _clear_the_level(GameState.level)
    GameState.next_stage()

    assert GameState.lives == remaining


@missing("a next stage to play", when=not opens_a_next_stage(),
         raises=AttributeError)
@verifies("src.game_state.GameStateModel.next_stage")
def test_the_next_stage_counts_up(
        write_config: Callable[[str], str]) -> None:
    """The stage number goes up by one."""

    Config.load_from_file(write_config('{"level_time": 500}'))
    GameState.reset()
    first_stage: int = GameState.stage
    _clear_the_level(GameState.level)
    GameState.next_stage()

    assert GameState.stage == first_stage + 1


@missing("a next stage to play", when=not opens_a_next_stage(),
         raises=AttributeError)
@verifies("src.game_state.GameStateModel.next_stage")
def test_the_game_has_at_least_ten_stages() -> None:
    """The subject asks for ten levels or more."""

    stages = 1
    while GameState.next_stage():
        stages += 1

    assert stages >= 10
