"""
Deterministic replay of recorded counterexamples, the memory of the
property suite: :mod:`discopy.axioms` documents the recording protocol.
"""

from typing import NamedTuple

import pytest

from discopy import biclosed, braided, cat, compact, pivotal, ribbon
from discopy.axioms import GENERATORS, Axiom, AxiomFailure, Relabelling
from discopy.utils import AxiomError, factory_name


class Counterexample(NamedTuple):
    """
    A counterexample once found against a law: the bound axiom itself and
    the very arguments the search shrunk the failure to.
    """
    axiom: Axiom
    args: tuple
    reason: str


COLLAPSE = Relabelling(tuple(
    (cat.Ob(name), cat.Ob("a")) for name in GENERATORS))
"""
The relabelling the search shrunk to: every generator sent to the first.

It names all of them because every functor the strategy builds does, see
:obj:`discopy.axioms.GENERATORS`. The images are what shrinking landed on
rather than what the bug needs: composing the identity functor on the
left preserves its action but compares unequal (#648).
"""

COUNTEREXAMPLES = (
    Counterexample(
        axiom=cat.Functor.unitality,
        args=(cat.Functor(ob_map=COLLAPSE, ar_map=COLLAPSE), ),
        reason="Composing the identity functor on the left of a mapping "
               "preserves its action but compares unequal (#648)."),
    Counterexample(
        axiom=braided.Diagram.braid_naturality,
        args=(braided.Box("f", braided.Ty("a"), braided.Ty("a")),
              braided.Box("g", braided.Ty("a"), braided.Ty("a"))),
        reason="A free braid is a box, so naturality only holds up to the "
               "braid relations that free diagrams do not quotient by."),
    Counterexample(
        axiom=biclosed.Diagram.currying_left,
        args=(biclosed.Eval(biclosed.Ty("a") << biclosed.Ty("a")),
              biclosed.Ty("a"), biclosed.Ty("a")),
        reason="A free currying is a bubble, equal to its evaluation only "
               "semantically."),
    Counterexample(
        axiom=biclosed.Diagram.currying_right,
        args=(biclosed.Eval(
                  biclosed.Ty("a") >> biclosed.Ty("a"), left=False),
              biclosed.Ty("a"), biclosed.Ty("a")),
        reason="A free currying is a bubble, equal to its evaluation only "
               "semantically."),
    Counterexample(
        axiom=pivotal.Diagram.pivotality,
        args=(pivotal.Diagram.id(pivotal.Ty("a")), ),
        reason="The two transposes of a free pivotal diagram are distinct "
               "diagrams, already on the identity wire."),
    Counterexample(
        axiom=ribbon.Diagram.twist_as_trace,
        args=(pivotal.Ty("a"), ),
        reason="A free twist is a box, not the trace of a braid."),
    Counterexample(
        axiom=compact.CMap.bifunctoriality,
        args=(compact.Box("f", compact.Ty("a"), compact.Ty("a")).to_map(),
              compact.Box("g", compact.Ty("a"), compact.Ty("a")).to_map(),
              compact.Box("h", compact.Ty("a"), compact.Ty("a")).to_map(),
              compact.Box("k", compact.Ty("a"), compact.Ty("a")).to_map()),
        reason="Tensoring rows lists the boxes (f, g, h, k) where "
               "composing columns lists (f, h, g, k), and a map is "
               "compared with its boxes in listed order."),
    Counterexample(
        axiom=compact.CMap.dagger_monoidality,
        args=(compact.Box("f", compact.Ty("a"), compact.Ty("a")).to_map(),
              compact.Box("g", compact.Ty("a"), compact.Ty("a")).to_map()),
        reason="The dagger reverses the box list where the tensor of "
               "daggers preserves it."),
    Counterexample(
        axiom=compact.CMap.braid_naturality,
        args=(compact.Box("f", compact.Ty("a"), compact.Ty("a")).to_map(),
              compact.Box("g", compact.Ty("a"), compact.Ty("a")).to_map()),
        reason="Sliding two boxes past the braid exchanges their places "
               "in the box list, which a map distinguishes."),
    Counterexample(
        axiom=compact.CMap.trace_dinaturality_left,
        args=(compact.Box(
                  "f", compact.Ty("a", "a"), compact.Ty("a", "a")).to_map(),
              compact.Box("g", compact.Ty("a"), compact.Ty("a")).to_map()),
        reason="Sliding a box around the loop moves it from one end of "
               "the box list to the other, which a map distinguishes."),
    Counterexample(
        axiom=compact.CMap.trace_dinaturality_right,
        args=(compact.Box(
                  "f", compact.Ty("a", "a"), compact.Ty("a", "a")).to_map(),
              compact.Box("g", compact.Ty("a"), compact.Ty("a")).to_map()),
        reason="Sliding a box around the loop moves it from one end of "
               "the box list to the other, which a map distinguishes."),
)


def counterexample_parameters():
    """
    One parameter per record, a strict xfail while its axiom is declared
    broken: the day the bug is fixed the record fails as an unexpected pass
    until the ``.failing`` declaration moves.
    """
    for axiom, args, reason in COUNTEREXAMPLES:
        marks = pytest.mark.xfail(
            reason=reason, raises=(AssertionError, AxiomError), strict=True)\
            if axiom.broken else ()
        yield pytest.param(
            axiom, args, marks=marks,
            id=f"{factory_name(axiom.category)}.{axiom.name}")


@pytest.mark.parametrize("axiom, args", counterexample_parameters())
def test_counterexample(axiom, args):
    """
    Check an axiom on a recorded counterexample.

    A broken axiom's failure carries the equation, which the record must
    falsify: its cell xfails while the bug stands and passes — visibly,
    as an expected pass — the day the bug is fixed.
    """
    try:
        assert axiom(*args)
    except AxiomFailure as failure:
        assert failure.equation
