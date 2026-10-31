"""Reports what a run found where a reviewer reads it: the game's code.

A test names what it covers with @verifies, and its failure is reported
on that code instead of on the assertion that caught it. A test naming
nothing is reported on the deepest file of the game its failure went
through, and a failure going through none of them is written to the file
the workflow posts as a comment of the pull request.
"""

import inspect
import os
import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Optional

import pytest

Site = tuple[str, int]

_ROOT: Path = Path(__file__).resolve().parent.parent


def verifies(target: str) -> pytest.MarkDecorator:
    """Returns a marker naming the code a test covers.

    target -- dotted path of the code, classes rather than their instances
    """

    return pytest.mark.verifies(target)


def declared_site(item: pytest.Item) -> Optional[Site]:
    """Returns the file and line of the code a test declared covering.

    item -- the test to read the marker of
    Returns None when it declares nothing this branch holds
    """

    marker: Optional[pytest.Mark] = item.get_closest_marker("verifies")
    if marker is None:
        return None
    return _source_site(str(marker.args[0]))


def crash_site(
        excinfo: Optional[pytest.ExceptionInfo[BaseException]]
) -> Optional[Site]:
    """Returns the deepest file of the game a failure went through.

    excinfo -- what the test raised, None when it raised nothing
    Returns None when no file of the game took part in the failure
    """

    if excinfo is None:
        return None
    for entry in reversed(list(excinfo.traceback)):
        path: Path = Path(str(entry.path)).resolve()
        if any(path.is_relative_to(_ROOT / package)
               for package in ("src", "manage_screen")):
            return str(path), entry.lineno + 1
    return None


class Review:
    """Reports the failures and the gaps of a run to its reviewer.

    Public Functions:
        failure -- keeps a failed test, for the code it covers
        gap -- warns about the tests a gap held back
        close -- reports everything kept, one review per code site
    """

    def __init__(self) -> None:
        """Creates a review with nothing reported yet."""

        self._in_actions: bool = bool(os.environ.get("GITHUB_ACTIONS"))
        self._sited: dict[Site, list[tuple[str, str]]] = {}
        self._loose: list[str] = []

    def failure(self, report: Any, outcome: str) -> None:
        """Keeps a failed test, for the code it covers when one is known.

        report -- the result pytest kept for the test
        outcome -- failed or error, as the run counted it
        """

        title: str = f"{report.nodeid} {outcome}"
        trace: str = str(report.longrepr)
        site: Optional[Site] = getattr(report, "review_site", None)
        if site is None:
            self._loose.append(f"### {title}\n\n```\n{trace}\n```")
        else:
            self._sited.setdefault(site, []).append((title, trace))

    def gap(self, gap: str, reports: list[Any]) -> None:
        """Warns about the tests a gap held back, failing nothing.

        gap -- the reason they were not run
        reports -- the results pytest kept for them
        """

        if not self._in_actions:
            return
        for report in reports:
            site: Optional[Site] = getattr(report, "review_site", None)
            if site is not None:
                _annotate("warning", site,
                          f"{len(reports)} test(s) not run", gap)
                return

    def close(self) -> None:
        """Reports every failure kept, the tests of one code site together.

        GitHub keeps ten reviews per step, so a run failing in one place
        reports it once instead of losing the other places it touched.
        """

        for site, failures in self._sited.items():
            title, trace = failures[0]
            others: list[str] = [name for name, _ in failures[1:]]
            if others:
                title = f"{len(failures)} tests failed on this code"
                trace = "\n".join([trace, "", "failed here as well:",
                                   *others])
            if self._in_actions:
                _annotate("error", site, title, trace)
        if not self._in_actions or not self._loose:
            return
        body: str = "\n\n".join(
            ["## Unit tests",
             "No file of the game took part in these failures, so they "
             "are reported here."] + self._loose)
        try:
            # GitHub refuses a comment over 65536 characters
            (_ROOT / "review-comment.md").write_text(body[:65000],
                                                     encoding="utf-8")
        except OSError as error:
            print(f"could not write the review comment: {error}",
                  file=sys.stderr)


def _source_site(target: str) -> Optional[Site]:
    """Returns the file and first line of what a dotted path names.

    target -- the dotted path to look up
    Returns None when nothing with a source answers to it
    """

    found: Any = _looked_up(target)
    if isinstance(found, property):
        found = found.fget
    found = inspect.unwrap(getattr(found, "__func__", found))
    try:
        file: Optional[str] = inspect.getsourcefile(found)
        line: int = inspect.getsourcelines(found)[1]
    except (OSError, TypeError):
        return None
    if file is None:
        return None
    return str(Path(file).resolve()), max(line, 1)


def _looked_up(target: str) -> Any:
    """Returns what a dotted path names, None when nothing answers to it.

    target -- the dotted path to walk, its longest module prefix first
    """

    parts: list[str] = target.split(".")
    for cut in range(len(parts), 0, -1):
        try:
            found: Any = import_module(".".join(parts[:cut]))
        except Exception:
            # a branch missing the module simply has no site to report on
            continue
        for name in parts[cut:]:
            found = getattr(found, name, None)
        return found
    return None


def _annotate(level: str, site: Site, title: str, message: str) -> None:
    """Prints one GitHub annotation on stdout.

    level -- error, warning or notice
    site -- the file and line the annotation is shown on
    title -- the heading the annotation is given
    message -- what it says under the heading
    """

    path, line = site
    body: str = _escaped(_capped(message), in_message=True)
    print(f"::{level} file={_escaped(_in_repository(path))},line={line},"
          f"title={_escaped(title)}::{body}")


def _in_repository(path: str) -> str:
    """Returns a path as the repository holds it, GitHub reading no other.

    path -- the absolute path of the file
    """

    try:
        return str(Path(path).relative_to(_ROOT))
    except ValueError:
        return path


def _capped(message: str) -> str:
    """Returns a message short enough for one annotation.

    message -- the report to shorten
    """

    if len(message) <= 8000:
        return message
    return f"[cut to its last 8000 characters]\n{message[-8000:]}"


def _escaped(text: str, *, in_message: bool = False) -> str:
    """Returns a text a GitHub annotation can carry.

    text -- what to escape
    in_message -- True for the body, which keeps colons and commas
    """

    escaped: str = (text.replace("%", "%25").replace("\r", "%0D")
                    .replace("\n", "%0A"))
    if in_message:
        return escaped
    return escaped.replace(":", "%3A").replace(",", "%2C")
