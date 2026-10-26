"""Markers for what the game does not do yet, so the suite stays green.

Every marker names the gap it waits on. The branch under test is probed
rather than named, so a branch that fills the gap runs the test for real
instead of reporting it as expected to fail. Grep this module's two names
to list every gap the suite knows.
"""

from typing import Optional

import pytest

_Raises = type[BaseException] | tuple[type[BaseException], ...]


def missing(feature: str, *, when: bool = True,
            raises: Optional[_Raises] = None) -> pytest.MarkDecorator:
    """Returns a marker for a test waiting on an unwritten feature.

    feature -- what the game still has to implement
    when -- False on a branch that implements it, which runs the test
    raises -- the failure the gap produces, so another one stays red
    """

    return pytest.mark.xfail(condition=when, strict=True, raises=raises,
                             reason=f"not implemented: {feature}")


def known_bug(defect: str, *, when: bool = True,
              raises: Optional[_Raises] = None) -> pytest.MarkDecorator:
    """Returns a marker for a test that a reported defect keeps red.

    defect -- the defect, as reported to the author
    when -- False on a branch where it is fixed, which runs the test
    raises -- the failure the defect produces, so another one stays red
    """

    return pytest.mark.xfail(condition=when, strict=True, raises=raises,
                             reason=f"known bug: {defect}")
