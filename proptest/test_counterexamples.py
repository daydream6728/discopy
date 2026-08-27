"""
Deterministic replay of recorded counterexamples, the memory of the
property suite: see PROPTEST.md for the recording protocol.
"""

from typing import NamedTuple

import pytest

from discopy import hopf
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


INTERTWINER = hopf.Intertwiner[hopf.Double(hopf.Algebra.cyclic(2))]

ANYONS = INTERTWINER.ob.direct_sum([
    INTERTWINER.ob.anyon(0, -1), INTERTWINER.ob.anyon(1, 1)])

COUNTEREXAMPLES = (
    Counterexample(
        axiom=Matrix[int].copy_cocommutativity,
        args=(2, ),
        reason="Matrix.copy(x, n) is wrong for x, n >= 2 (#606)"),
    Counterexample(
        axiom=INTERTWINER.reidemeister_1_cap,
        args=(ANYONS @ ANYONS, ),
        reason="Reidemeister 1 fails on a composite module, where the "
               "swap is the braiding and the pivotal correction fires "
               "on a structural comparison with the unit."),
    Counterexample(
        axiom=INTERTWINER.reidemeister_1_cup,
        args=(ANYONS @ ANYONS, ),
        reason="Reidemeister 1 fails on a composite module, where the "
               "swap is the braiding and the pivotal correction fires "
               "on a structural comparison with the unit."),
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
