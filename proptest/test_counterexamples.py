"""
Deterministic replay of recorded counterexamples, the memory of the
property suite: see PROPTEST.md for the recording protocol.
"""

from typing import NamedTuple

import pytest

from discopy.matrix import Matrix
from discopy.testing import Axiom, assert_verdict
from discopy.utils import factory_name


class Counterexample(NamedTuple):
    """
    A counterexample once found against a law: the bound axiom itself and
    the very arguments the search shrunk the failure to.
    """
    axiom: Axiom
    args: tuple
    reason: str


COUNTEREXAMPLES = (
    Counterexample(
        axiom=Matrix[int].copy_cocommutativity,
        args=(2, ),
        reason="Matrix.copy(x, n) is wrong for x, n >= 2 (#606)"),
)


def counterexample_parameters():
    """ One parameter per record, xfail while its axiom is declared broken. """
    for axiom, args, reason in COUNTEREXAMPLES:
        marks = pytest.mark.xfail(reason=reason) if axiom.broken else ()
        yield pytest.param(
            axiom, args, marks=marks,
            id=f"{factory_name(axiom.carrier)}.{axiom.name}")


@pytest.mark.parametrize("axiom, args", counterexample_parameters())
def test_counterexample(axiom, args):
    """ Check an axiom on a recorded counterexample. """
    assert_verdict(axiom, axiom(*args))
