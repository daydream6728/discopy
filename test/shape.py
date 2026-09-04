# -*- coding: utf-8 -*-

""" Tests for discopy.shape """

from pytest import raises

from hypothesis import find, strategies as st

from discopy import cat, markov, monoidal
from discopy.shape import Model, Sample, Shape
from discopy.utils import AxiomError


def dice():
    return Sample(lambda: st.integers(1, 6), (), (int, ))


def test_Sample_then():
    double = Sample.pure(lambda n: 2 * n, (int, ), (int, ))
    assert find((dice() >> double)(), lambda n: n > 10) == 12
    with raises(AxiomError):
        dice() >> Sample.pure(lambda x, y: x, (int, int), (int, ))


def test_Sample_tensor():
    assert find((dice() @ dice())(), lambda pair: pair == (6, 1)) == (6, 1)


def test_Sample_copy():
    equal = dice() >> Sample.copy((int, ))
    assert find(equal(), lambda pair: pair[0] == pair[1] > 3) == (4, 4)
    assert find(
        (dice() >> Sample.discard((int, )))(), lambda x: x == ()) == ()


def test_Sample_permutation():
    values = Sample.pure(lambda: (0, 1, 2), (), (int, int, int))
    rotate = Sample.permutation([1, 2, 0], 3 * [(int, )])
    assert find((values >> rotate)(), lambda _: True) == (1, 2, 0)


def test_Sample_functor():
    x = markov.Ty('x')
    draw = markov.Box('draw', markov.Ty(), x)
    add = markov.Box('add', x @ x, x)
    diagram = draw >> markov.Copy(x) >> add
    F = markov.Functor(
        ob_map={x: int},
        ar_map={draw: lambda: st.integers(1, 6),
                add: lambda a, b: st.just(a + b)},
        cod=Sample)
    assert find(F(diagram)(), lambda n: n % 2 == 0 and n > 6) == 8


def test_grid_cat():
    pair = Shape.grid(2, 1)
    f, g = find(pair.strategy(cat.Arrow), lambda _: True)
    assert f.cod == g.dom
    assert isinstance(f >> g, cat.Arrow)


def test_grid_monoidal():
    pair = Shape.grid(2, 1)
    f, g = find(
        pair.strategy(monoidal.Diagram),
        lambda model: len(next(iter(model))) > 0)
    assert f.cod == g.dom


def test_grid_bound():
    x, y = monoidal.Ty('x'), monoidal.Ty('y')
    triple = Shape.grid(3, 1)
    f, g, h = find(
        triple.strategy(monoidal.Diagram, dom=x, cod=y), lambda _: True)
    assert f.dom == x and f.cod == g.dom and g.cod == h.dom and h.cod == y


def test_Model_typing():
    x, y = monoidal.Ty('x'), monoidal.Ty('y')
    f = monoidal.Box('f', x, y)
    pair = Shape.grid(2, 1)
    with raises(AxiomError):
        Model(pair, monoidal.Diagram,
              obs={"x00": x, "x10": y, "x20": x}, ars={"f00": f, "f10": f})


def test_TraceNaturality():
    from discopy import symmetric
    from discopy.shape import TraceNaturalityLeft
    traced, u, sliding = find(
        TraceNaturalityLeft.strategy(symmetric.Diagram), lambda _: True)
    assert traced.dom == u @ sliding.cod and traced.cod == u @ sliding.dom
    assert len(traced) >= 1 <= len(sliding)


def test_TraceSuperposing():
    from discopy import symmetric
    from discopy.shape import TraceSuperposing
    traced, obj = find(
        TraceSuperposing.strategy(symmetric.Diagram), lambda _: True)
    assert traced == symmetric.Id(traced.dom) and len(traced.dom) == 1


def test_Currying():
    from discopy import closed
    from discopy.shape import LeftCurrying, RightCurrying
    arrow, base, exponent = find(
        LeftCurrying.strategy(closed.Diagram), lambda _: True)
    assert arrow == closed.Diagram.ev(base, exponent, left=True)
    arrow, base, exponent = find(
        RightCurrying.strategy(closed.Diagram), lambda _: True)
    assert arrow == closed.Diagram.ev(base, exponent, left=False)


def test_Feedback():
    from discopy import feedback
    from discopy.shape import FeedbackJoining, FeedbackVanishing
    arrow, unit = find(
        FeedbackVanishing.strategy(feedback.Diagram), lambda _: True)
    assert unit == feedback.Ty()
    arrow, mem = find(
        FeedbackJoining.strategy(feedback.Diagram), lambda _: True)
    assert len(mem) == 2
    assert arrow.dom[-2:] == mem.delay() and arrow.cod[-2:] == mem


def test_sorted_objects():
    from discopy.shape import Atomic, NonEmpty, Small
    assert len(find(
        Atomic.strategy(monoidal.Diagram), lambda _: True).value) == 1
    assert len(find(
        NonEmpty.strategy(monoidal.Diagram), lambda _: True).value) >= 1
    assert len(find(
        Small.strategy(monoidal.Diagram), lambda _: True).value) <= 1


def test_Bifunctor():
    from discopy.shape import Bifunctor
    f, g, h, k = find(
        Bifunctor.strategy(monoidal.Diagram),
        lambda model: any(len(cell) for cell in model))
    assert f.cod == h.dom and g.cod == k.dom
    assert (f @ g >> h @ k).dom == f.dom @ g.dom
