from pytest import raises

from discopy import *
from discopy.stream import *

def test_errors():
    T, S = Ty[python.Ty], Stream[python.Function]
    with raises(ValueError):
        S(lambda x: x, mem=T(int))
    dom = cod = mem = T(int)
    now = python.Function(lambda x, y: (x + y, x - y), (int, int), (int, int))
    with raises(AxiomError):
        S(now, dom, cod)
    with raises(AxiomError):
        S(now, dom, cod, mem.head)
    with raises(AxiomError):
        non_constant = T(dom, _later=lambda: dom)
        S(now, non_constant, cod, mem)
    mismatched_cod = python.Function(lambda x: x, (int, ), (int, ))
    with raises(AxiomError, match=r"str.*!= .*int"):
        S(mismatched_cod, T(int), T(str))


def test_python_stream():
    T, S = Ty[python.Ty], Stream[python.Function]
    x, y, m = int, bool, str
    dom = T(x) @ T(m).delay()
    cod = T(y) @ T(m)
    now = python.Function(lambda n: (bool(n % 2), str(n)), (x, ), (y, m))
    later = python.Function(
        lambda n, s: (bool(n % 2), s + " " + str(n)), (x, m), (y, m))
    s = S(now, dom, cod, _later=lambda: S(later))
    s.check_later()
    s.unroll().check_later()
    fb = s.feedback(dom=T(x), cod=T(y), mem=T(m))
    assert fb.unroll(2).now(1, 2, 3) == (True, False, True, '1 2 3')


def test_sequence_box_of_its_category():
    """ A stream builds the boxes of the category it is over. """
    from discopy import markov, tensor
    for category in (symmetric.Diagram, markov.Diagram):
        x = Ty.sequence(category.ob('x'))
        box = Stream[category].sequence("f", x, x).now
        assert type(box) is category.box_factory
    dim = Ty[tensor.Dim](tensor.Dim(2))  # A constant stream of dimensions.
    box = Stream[tensor.Diagram].sequence("f", dim, dim).now
    assert type(box) is tensor.Box is tensor.Diagram.box_factory


def test_feedback_forms():
    from pytest import raises
    x, y, m = (Ty.sequence(symmetric.Ty(name)) for name in "xym")
    f = Stream.sequence("f", x @ m.delay(), y @ m)
    unrolled = f.feedback(dom=x, cod=y, mem=m).unroll(2).now
    for fb in (f.feedback(), f.feedback(1), f.feedback(mem=m)):
        assert fb.unroll(2).now == unrolled
    with raises(TypeError):
        f.feedback(1, mem=m)
    with raises(NotImplementedError):
        f.feedback(left=True)
    with raises(NotImplementedError):
        f.feedback(cod=y)
    with raises(ValueError):
        f.feedback(3)


def test_feedback_of_no_memory():
    x = symmetric.Ty('x')
    constant = Stream(symmetric.Box('f', x, x))
    assert constant.feedback(0) == constant == constant.feedback(mem=Ty())
    f = Stream.sequence("f", *map(Ty.sequence, "xy"))
    assert f.feedback(0) is f and f.feedback(mem=Ty()) is f


def test_last_and_without():
    from pytest import raises
    X, Y = map(Ty.sequence, "xy")
    XY = X @ Y
    assert [XY.last(1).later.now, XY.without(Y).later.now] == [
        symmetric.Ty("y1"), symmetric.Ty("x1")]
    with raises(ValueError):
        XY.without(X)


def test_feedback_laws():
    from pytest import raises
    from discopy.abc import FeedbackCategory
    from discopy.axioms import AxiomFailure
    x, y, m, n, w, z = (Ty.sequence(symmetric.Ty(name)) for name in "xymnwz")
    f = Stream.sequence('f', x @ (m @ n).delay(), y @ m @ n)
    loop = (x, y, m, n, f) + tuple(Stream.sequence(name, dom, cod) for name, (
        dom, cod) in zip("ghke", [(w, x), (y, z), (m @ n, m @ n), (w, z)]))
    up_to = lambda stream: stream.unroll(2).now.to_hypergraph()
    assert FeedbackCategory.vanishing.bind(Stream).modulo(up_to)(f)
    for law in ("joining", "strength", "tightening"):
        assert getattr(FeedbackCategory, law).bind(Stream).modulo(up_to)(loop)
    assert not FeedbackCategory.sliding.bind(Stream).modulo(up_to)(loop)
    with raises(AxiomFailure):
        Stream.sliding(loop)
