"""Markers for what the game does not do yet, so the suite stays green.

Every marker names the gap it waits on, and strict=True turns the test red
again as soon as the gap is filled, which is the signal to delete the
marker. Grep this module's two names to list every gap the suite knows.
"""

import pytest


def missing(feature: str) -> pytest.MarkDecorator:
    """Returns a marker for a test waiting on an unwritten feature.

    feature -- what the game still has to implement
    """

    return pytest.mark.xfail(strict=True,
                             reason=f"not implemented: {feature}")


def known_bug(defect: str) -> pytest.MarkDecorator:
    """Returns a marker for a test that a reported defect keeps red.

    defect -- the defect, as reported to the author
    """

    return pytest.mark.xfail(strict=True, reason=f"known bug: {defect}")
