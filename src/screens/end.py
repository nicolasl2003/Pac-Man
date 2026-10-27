from typing import Any

from manage_screen.renderer import Color, InputEvent, PygameRenderer
from manage_screen.screen import Screen

from src import Config, GameState, Level
from ..scores import save_score


class EndScreen(Screen):
    """The screen closing a run, won or lost, where the name is typed.

    Public Variables:
        won -- Whether the run ended on the last level completed
        score -- The score the run ended with
        name -- The name typed so far

    Public Functions:
        on_enter -- Reads the outcome of the run that just ended
        handle_events -- Types the name and saves it on Enter
        update -- Changes nothing between two frames
        draw -- Draws the outcome, the score and the name
    """

    won: bool
    score: int
    name: str

    def on_enter(self, **kwargs: Any) -> None:
        """Reads the outcome and the score of the run that just ended.

        kwargs -- The context of the screen change, the renderer included
        """

        self.won = GameState.level.state == Level.State.WON
        self.score = GameState.score
        self.name = ""

    def handle_events(self, events: list[InputEvent]) -> str | None:
        """Types the name, and saves it with the score on Enter.

        Escape leaves without saving.
        events -- The inputs of the frame
        Returns the name of the next screen
            or None to stay on this one
        """

        for event in events:
            match event.kind, event.key:
                case "QUIT", _:
                    return ("QUIT")
                case "KEY", "ENTER":
                    save_score(self.name, self.score)
                    return ("MENU")
                case "KEY", "ESCAPE":
                    return ("MENU")
                case "KEY", "BACKSPACE":
                    self.name = self.name[:-1]
                case "KEY", str(typed) if (len(typed) == 1
                                           and len(self.name)
                                           < Config.name_length):
                    self.name += typed
        return (None)

    def update(self, dt: float) -> None:
        """Changes nothing between two frames.

        dt -- The time elapsed since the previous frame
        """

        return (None)

    def draw(self, renderer: PygameRenderer) -> None:
        """Draws the outcome, the score and the name being typed.

        renderer -- The renderer to draw with
        """

        renderer.clear()
        if (self.won):
            self._draw_centered(renderer, "CONGRATULATIONS!", 80,
                                (255, 255, 0), 48)
            self._draw_centered(renderer, "every level completed", 160,
                                (255, 255, 255), 24)
        else:
            self._draw_centered(renderer, "GAME OVER", 80, (255, 0, 0), 48)
        self._draw_centered(renderer, f"score {self.score}", 240,
                            (255, 255, 255), 36)
        if (GameState.highscore > self.score):
            self._draw_centered(renderer, f"best {GameState.highscore}", 290,
                                (180, 180, 180), 24)
        self._draw_centered(renderer, "enter your name", 400,
                            (255, 255, 255), 24)
        self._draw_centered(renderer, f"{self.name}_", 450,
                            (255, 255, 0), 36)
        self._draw_centered(renderer, "ENTER to save, ESC to skip", 560,
                            (180, 180, 180), 24)

    def _draw_centered(self, renderer: PygameRenderer, text: str, y: int,
                       color: Color, font_size: int) -> None:
        """Draws one line of text centered on the window.

        renderer -- The renderer to draw with
        text -- The line to draw
        y -- The distance from the top of the window
        color -- The color of the line
        font_size -- The height of the font to use
        """

        width: int = renderer.get_text_size(text, font_size)[0]
        renderer.draw_text(text, (renderer.width - width) // 2, y,
                           color, font_size)
