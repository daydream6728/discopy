from pytest import raises, warns

from discopy.feedback import *
from discopy.utils import AxiomError


def test_invalid_inputs():
    with raises(NotImplementedError):
        Ty('x').delay(-1)
    with raises(ValueError):
        HeadOb(Wire('x').delay())
    with raises(ValueError):
        TailOb(Wire('x').delay())


def test_trace_is_a_feedback_diagram():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x @ y, x @ y)
    for trace in (f.trace(), f.trace(left=True)):
        assert isinstance(trace, Trace) and isinstance(trace, Diagram)
        assert isinstance(trace >> trace, Diagram)
        assert trace.delay() == f.delay().trace(left=trace.left)
        assert trace.delay(2) == trace.delay().delay()
        assert trace.delay() >> trace.delay() == (trace >> trace).delay()


def test_feedback_with_a_memory_of_many_wires():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x @ (y @ z).delay(), x @ y @ z)
    for fb in (f.feedback(mem=y @ z), f.feedback(dom=x, cod=x, mem=y @ z)):
        assert fb == f.feedback(mem=z).feedback(mem=y)
        assert (fb.dom, fb.cod) == (x, x)
    assert f.feedback(mem=Ty()) == f


def test_delayed_Box_to_tree():
    from discopy.utils import dumps, loads
    x, y = Ty('x'), Ty('y')
    for box in (Box('f', x, y), Box('f', x, y, data=42).dagger()):
        for delayed in (box, box.delay(), box.delay(2)):
            assert loads(dumps(delayed)) == delayed
            assert loads(dumps(delayed)).time_step == delayed.time_step


def test_Feedback_to_tree():
    from discopy.utils import dumps, loads
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x @ (y @ z).delay(), x @ y @ z)
    for fb in (f.feedback(mem=z), f.feedback(mem=y @ z), Feedback(f, mem=y @ z)):
        assert loads(dumps(fb)) == fb
        assert loads(dumps(fb)).mem == fb.mem


def test_Head_Tail_FollowedBy_to_tree():
    from discopy.utils import dumps, loads
    x, y = Ty(Wire('x', is_constant=False)), Ty('y')
    f = Box('f', x, y)
    for term in (x.head, x.tail, x.head.delay(), f.head, f.tail, f.tail.delay(2),
                 FollowedBy(x), FollowedBy(x, is_dagger=True).delay()):
        assert loads(dumps(term)) == term


def test_trace_repr():
    from discopy import feedback
    trace = Box('f', 'x', 'x').trace()
    assert repr(trace) == "feedback.Trace(feedback.Box('f', "\
        "feedback.Ty(feedback.Wire('x')), feedback.Ty(feedback.Wire('x'))))"
    assert eval(repr(trace)) == trace
    assert repr(Box('f', 'x', 'x').trace(left=True)).endswith(", left=True)")


def test_trace_error():
    with raises(AxiomError):
        Box('f', 'x', 'y').trace()


def test_trace_dagger():
    f = Box('f', 'x', 'x')
    assert f.trace().dagger() == f.dagger().trace()


def test_trace_vanishing():
    from discopy import compact, matrix, ribbon
    from discopy.python import additive, multiplicative

    x = compact.Ty('x')
    f = compact.Box('f', x @ x, x @ x)
    assert f.trace(0) == f
    assert f.to_hypergraph().trace(0) == f.to_hypergraph()
    assert f.to_map().trace(0) == f.to_map()
    assert f.to_drawing().trace(0) == f.to_drawing()

    y = ribbon.Ty('y')
    g = ribbon.Box('g', y @ y, y @ y)
    assert g.trace(0) == g

    assert matrix.Matrix[bool].swap(1, 1).trace(0)\
        == matrix.Matrix[bool].swap(1, 1)

    h = additive.Function(lambda i, tag=0: (i, tag), (int, int), (int, int))
    assert h.trace(0) == h

    k = multiplicative.Function(lambda i, j: (i, j), (int, int), (int, int))
    assert k.trace(0) == k


def test_Sum():
    f = Box('f', 'x', 'x')
    assert Sum([f]) == f
    assert isinstance(f + f, Sum) and (f + f).terms == (f, f)
    image = Functor(lambda x: x, {f: f + f})(f)
    assert isinstance(image, Sum) and image.terms == (f, f)


def test_trace_serialisation():
    from discopy.utils import dumps, loads
    from discopy import symmetric
    f = Box('f', 'x', 'x')
    for trace in (f.trace(), f.trace(left=True)):
        assert loads(dumps(trace)) == trace
    x = symmetric.Ty('x')
    swap = symmetric.Swap(x, x)
    assert loads(dumps(swap.trace(left=True))) == swap.trace(left=True)


def test_trace_foliation():
    x = Ty('x')
    f, g = Box('f', x @ x, x @ x), Box('g', x, x)
    beside, below = f.trace() @ g, f.trace() >> g
    assert beside.foliation().boxes == [f.trace(), g]
    assert len(beside.foliation()) == 1 and beside.depth() == 1
    assert below.foliation() == below and below.depth() == 2


def test_traced_is_deprecated():
    from discopy import feedback, traced
    with warns(DeprecationWarning):
        assert traced.Diagram is feedback.Diagram
    with warns(DeprecationWarning):
        assert traced.Trace is feedback.Trace


def test_feedback_forms():
    x, m = Ty('x'), Ty('m')
    f = Box('f', x @ m.delay(), x @ m)
    assert f.feedback() == f.feedback(1) == f.feedback(mem=m)\
        == f.feedback(cod=x) == f.feedback(dom=x, cod=x, mem=m)
    with raises(TypeError):
        f.feedback(1, mem=m)
    with raises(ValueError):
        f.feedback(3)


def test_trace_is_an_undelayed_feedback():
    x, m = Ty('x'), Ty('m')
    f, g = Box('f', x @ m, x @ m), Box('g', x @ m.delay(), x @ m)
    assert isinstance(f.feedback(), Trace) and f.feedback() == f.trace()
    assert isinstance(g.feedback(), Feedback)
    assert not isinstance(g.feedback(), Trace)
    assert str(f.trace(mem=m)) == "Trace(f)"
    assert str(g.feedback()) == "Feedback(g)"
    assert f.trace(dom=x, cod=x, mem=m) == f.trace()
    with raises(AxiomError):
        g.trace()
    with raises(AxiomError):
        Feedback(f)


def test_left_feedback():
    x, m = Ty('x'), Ty('m')
    f = Box('f', m.delay() @ x, m @ x)
    assert f.feedback(left=True) == Feedback(f, left=True)
    assert f.feedback(left=True).delay() == f.delay().feedback(left=True)
    assert str(f.feedback(left=True)) == "Feedback(f, left=True)"


def test_traced_category_feedback_is_its_trace():
    from discopy.matrix import Matrix
    f, one = Matrix[bool]([[1, 1], [0, 0]], 2, 2), Matrix.ob(1)
    assert f.feedback() == f.feedback(mem=one) == f.trace()
    assert f.feedback(mem=one, left=True) == f.trace(left=True)
    assert f.delay() is f
    with raises(TypeError):
        f.feedback(1, mem=one)


def test_feedback_laws_on_a_traced_category():
    from discopy.axioms import Loop
    from discopy.matrix import Matrix
    M = Matrix[bool]
    x, y, m, n = 1, 1, 1, 1
    f = M([1, 0, 1, 1, 0, 1, 1, 0, 1], x + m + n, y + m + n)
    g, h, k, e = M([1], 1, x), M([0, 1], y, 2), M.swap(1, 1), M.id(1)
    loop = Loop[M](M.ob(x), M.ob(y), M.ob(m), M.ob(n), f, g, h, k, e)
    from discopy.abc import FeedbackCategory
    for law in ("vanishing", "joining", "strength", "tightening", "sliding"):
        args = (f, ) if law == "vanishing" else (loop, )
        assert getattr(FeedbackCategory, law).bind(M)(*args)


def test_time_stepped_wires_below_feedback():
    from discopy import markov, pivotal, frobenius
    x = markov.Ty('x')
    assert x.delay() != x and x.delay().inside[0].time_step == 1
    f = markov.Box('f', x @ x.delay(), x @ x)
    assert isinstance(f.feedback(), markov.Feedback)
    assert isinstance(markov.Box('g', x @ x, x @ x).trace(), markov.Trace)
    y = pivotal.Ty('y')
    assert y.delay().l == y.l.delay() and y.delay().l.l == y.delay()
    g = pivotal.Box('g', y @ y.delay(), y @ y)
    assert isinstance(g.feedback(), pivotal.Feedback)
    assert g.delay().time_step == 1
    assert frobenius.Ty('z').delay().r == frobenius.Ty('z').r.delay()
