# -*- coding: utf-8 -*-

"""
One test for each shape of :mod:`discopy.shape` as the axioms use it: its
constructor accepts valid images and rejects badly typed ones, and its
derived search strategy reaches every shape of argument the axioms expect.
Whether the axioms hold is checked over every category in ``proptest/``.
"""

from hypothesis import find
from pytest import raises

from discopy import biclosed, cat, feedback, monoidal, traced
from discopy.shape import (
    Atomic, Bifunctor, BoundaryConnected, ComposablePair, ComposableTriple,
    FeedbackJoining, FeedbackVanishing, HomogeneousMemory, HorizontalPair,
    LeftCurrying, NonEmpty, RightCurrying, Small, TraceDinaturalityLeft,
    TraceDinaturalityRight, TraceNaturalityLeft, TraceNaturalityRight,
    TraceSuperposing)
from discopy.testing import Natural, axiom
from discopy.utils import AxiomError


def test_Natural():
    assert Natural(2) @ Natural(3) == 5 == len(Natural(5))
    assert Natural.equation_factory(Natural(1), Natural(1))
    with raises(ValueError):
        Natural(-1)
    find(Natural.strategy(), lambda value: value == 0)
    find(Natural.strategy(), lambda value: value > 1)


def test_Atomic():
    x = monoidal.Ty('x')
    assert Atomic(x).value == x
    find(Atomic.strategy(monoidal.Ty), lambda model: len(model.value) == 1)


def test_NonEmpty():
    x = monoidal.Ty('x')
    assert NonEmpty(x).value == x
    find(NonEmpty.strategy(monoidal.Ty), lambda model: len(model.value) > 1)


def test_Small():
    x = monoidal.Ty('x')
    assert Small(x).value == x
    find(Small.strategy(monoidal.Ty), lambda model: len(model.value) == 1)


def test_ComposablePair():
    x, y = map(cat.Ob, "xy")
    f, g = cat.Box('f', x, y), cat.Box('g', y, x)
    assert tuple(ComposablePair(f, g)) == (f, g)
    with raises(ValueError):
        ComposablePair(f)
    with raises(AxiomError):
        ComposablePair(f, f)
    find(ComposablePair.strategy(cat.Arrow),
         lambda model: all(term.inside for term in model))


def test_ComposableTriple():
    x, y = map(cat.Ob, "xy")
    f, g = cat.Box('f', x, y), cat.Box('g', y, x)
    assert tuple(ComposableTriple(f, g, f)) == (f, g, f)
    with raises(AxiomError):
        ComposableTriple(f, f, f)
    find(ComposableTriple.strategy(cat.Arrow),
         lambda model: all(term.inside for term in model))


def test_HorizontalPair():
    x, y = map(monoidal.Ty, "xy")
    f, g = monoidal.Box('f', x, y), monoidal.Box('g', y, x)
    assert tuple(HorizontalPair(f, g)) == (f, g)
    with raises(ValueError):
        HorizontalPair(f)
    find(HorizontalPair.strategy(monoidal.Diagram),
         lambda model: all(term.boxes for term in model))


def test_Bifunctor():
    x, y = map(monoidal.Ty, "xy")
    f, g = monoidal.Box('f', x, y), monoidal.Box('g', y, x)
    assert tuple(Bifunctor(f, f, g, g)) == (f, f, g, g)
    with raises(AxiomError):
        Bifunctor(f, f, f, f)
    find(Bifunctor.strategy(monoidal.Diagram),
         lambda model: all(
             cells[column].boxes or cells[column + 2].boxes
             for cells in (tuple(model), ) for column in range(2)))


def test_BoundaryConnected():
    connected = BoundaryConnected[HorizontalPair[monoidal.Diagram]]
    find(connected.strategy(),
         lambda model: all(term.boxes for term in model))


def test_TraceSuperposing():
    x, y, z = map(traced.Ty, "xyz")
    assert tuple(TraceSuperposing(traced.Id(x), y)) == (traced.Id(x), y)
    with raises(AxiomError):
        TraceSuperposing(traced.Box('f', x, y), z)
    find(TraceSuperposing.strategy(traced.Diagram),
         lambda model: len(tuple(model)[1]) > 1)


def test_TraceNaturalityLeft():
    x, y = map(traced.Ty, "xy")
    f, g = traced.Box('f', x @ y, x @ x), traced.Box('g', x, y)
    assert tuple(TraceNaturalityLeft(f, x, g)) == (f, x, g)
    with raises(AxiomError):
        TraceNaturalityLeft(traced.Id(x @ y), x, traced.Id(x))
    find(TraceNaturalityLeft.strategy(traced.Diagram),
         lambda model: tuple(model)[2].dom != tuple(model)[2].cod)


def test_TraceNaturalityRight():
    x, y = map(traced.Ty, "xy")
    f, g = traced.Box('f', y @ x, x @ x), traced.Box('g', x, y)
    assert tuple(TraceNaturalityRight(f, x, g)) == (f, x, g)
    with raises(AxiomError):
        TraceNaturalityRight(traced.Id(x @ y), x, traced.Id(y))
    find(TraceNaturalityRight.strategy(traced.Diagram),
         lambda model: tuple(model)[2].dom != tuple(model)[2].cod)


def test_TraceDinaturalityLeft():
    x, y, z = map(traced.Ty, "xyz")
    f, g = traced.Box('f', x @ z, y @ z), traced.Box('g', y, x)
    assert tuple(TraceDinaturalityLeft(f, g)) == (f, g)
    with raises(AxiomError):
        TraceDinaturalityLeft(g, f)
    find(TraceDinaturalityLeft.strategy(traced.Diagram),
         lambda model: tuple(model)[1].dom != tuple(model)[1].cod)


def test_TraceDinaturalityRight():
    x, y, z = map(traced.Ty, "xyz")
    f, g = traced.Box('f', z @ x, z @ y), traced.Box('g', y, x)
    assert tuple(TraceDinaturalityRight(f, g)) == (f, g)
    with raises(AxiomError):
        TraceDinaturalityRight(g, f)
    traced_image, sliding = find(
        TraceDinaturalityRight.strategy(traced.Diagram),
        lambda model: tuple(model)[1].dom != tuple(model)[1].cod)
    assert traced_image.dom[-len(sliding.cod):] == sliding.cod
    assert traced_image.cod[-len(sliding.dom):] == sliding.dom


def test_LeftCurrying():
    x, y = map(biclosed.Ty, "xy")
    evaluation = biclosed.Diagram.ev(x, y, left=True)
    assert tuple(LeftCurrying(evaluation, x, y)) == (evaluation, x, y)
    with raises(AxiomError):
        LeftCurrying(evaluation, y, x)
    find(LeftCurrying.strategy(biclosed.Diagram),
         lambda model: tuple(model)[1] != tuple(model)[2])


def test_RightCurrying():
    x, y = map(biclosed.Ty, "xy")
    evaluation = biclosed.Diagram.ev(x, y, left=False)
    assert tuple(RightCurrying(evaluation, x, y)) == (evaluation, x, y)
    with raises(AxiomError):
        RightCurrying(evaluation, y, x)
    find(RightCurrying.strategy(biclosed.Diagram),
         lambda model: tuple(model)[1] != tuple(model)[2])


def test_FeedbackVanishing():
    x = feedback.Ty('x')
    f, unit = feedback.Box('f', x, x), feedback.Ty()
    assert tuple(FeedbackVanishing(f, unit)) == (f, unit)
    with raises(ValueError):
        FeedbackVanishing(f, x)
    find(FeedbackVanishing.strategy(feedback.Diagram),
         lambda model: tuple(model)[0].boxes)


def test_FeedbackJoining():
    x, y, z = map(feedback.Ty, "xyz")
    memory = y @ z
    f = feedback.Box('f', x @ memory.delay(), x @ memory)
    assert tuple(FeedbackJoining(f, memory)) == (f, memory)
    with raises(ValueError):
        FeedbackJoining(f, feedback.Ty())
    with raises(AxiomError):
        FeedbackJoining(feedback.Box('g', x @ memory, x @ memory), memory)
    with raises(AxiomError):
        FeedbackJoining(
            feedback.Box('g', x @ memory.delay(), x @ memory.delay()),
            memory)
    arrow, mem = find(FeedbackJoining.strategy(feedback.Diagram),
                      lambda model: tuple(model)[1][:1] != tuple(model)[1][1:])
    assert arrow.cod[-2:] == mem


def test_HomogeneousMemory():
    x, m = map(feedback.Ty, "xm")
    f = feedback.Box('f', x @ (m @ m).delay(), x @ m @ m)
    assert HomogeneousMemory(f, m @ m)
    n = feedback.Ty('n')
    g = feedback.Box('g', x @ (m @ n).delay(), x @ m @ n)
    with raises(AxiomError):
        HomogeneousMemory(g, m @ n)
    find(HomogeneousMemory.strategy(feedback.Diagram), lambda model: True)


def test_Axiom():
    @axiom
    def law(cls, f):
        """ Not an equation. """
        return cls.equation_factory(f)

    assert repr(law) == "Axiom(law)"
    assert [parameter.name for parameter in law.parameters] == ['f']
    assert cat.Arrow.unitality.carrier is cat.Arrow
    with raises(TypeError):
        law(cat.Id(cat.Ob('x')))
    assert law.bind(cat.Arrow)(cat.Id(cat.Ob('x')))


def test_inapplicable():
    class Carrier(cat.Arrow):
        unitality = cat.Arrow.unitality.inapplicable("No identities.")

    unitality, = (a for a in Carrier.axioms if a.name == "unitality")
    assert unitality() is NotImplemented
    assert unitality.__doc__ == "No identities."
    assert not unitality.parameters and not unitality.broken


# test_weaken lands on split/4-matrix: Matrix[int] is the first carrier
# whose axioms actually call Axiom.weaken.
