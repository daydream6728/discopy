from pytest import raises
from random import choice, seed

from discopy import *
from discopy.feedback import *


def test_invalid_inputs():
    with raises(NotImplementedError):
        Ty('x').delay(-1)
    with raises(ValueError):
        HeadOb(Wire('x').delay())
    with raises(ValueError):
        TailOb(Wire('x').delay())


def test_Diagram_repr():
    x = Ty('x')
    plus = Box('plus', x @ x, x)
    zero = Box('zero', Ty(), x.head)
    zero, one = Box('zero', Ty(), x.head), Box('one', Ty(), x.head)
    fib =  ((
            Copy(x) >> one @ Diagram.wait(x) @ x
            >> FollowedBy(x) @ x >> plus).delay()
        >> zero @ x.delay() >> FollowedBy(x) >> Copy(x)).feedback()
    assert eval(str(fib)) == fib
    assert eval(repr(fib)) == fib


def test_functor_python_stream():
    x = Ty('x')
    zero, wait = Box('zero', Ty(), x), Diagram.wait(x)
    F = Functor(
        ob_map={x: int},
        ar_map={zero: lambda: 0},
        cod=stream.Stream[python.Function])
    assert F(wait @ zero).unroll(2).now(1, 2, 3) == (0, ) + (1, 0) + (2, 0) + (3, )


def test_walk():
    seed(420)
    X, fby = Ty('X'), FollowedBy(Ty('X'))
    zero, rand, plus = Box('0', Ty(), X), Box('rand', Ty(), X), Box('+', X @ X, X)

    @Diagram.feedback
    @Diagram.from_callable(X.d, X @ X)
    def walk(x):
        y = fby(zero.head(), plus.d(rand.d(), x))
        return (y, y)

    F = Functor(
        ob_map={X: int},
        ar_map={zero: lambda: 0,
            rand: lambda: choice([-1, +1]),
            plus: lambda x, y: x + y},
        cod=stream.Stream[python.Function])

    assert F(walk).unroll(9).now()[:10] == (0, -1, 0, 1, 2, 1, 0, -1, 0, 1)
    assert F(walk).unroll(9).now()[:10] == (0, -1, -2, -1, 0, 1, 0, 1, 2, 1)
    assert F(walk).unroll(9).now()[:10] == (0, -1, 0, 1, 0, 1, 0, -1, 0, -1)

def test_fibonacci():
    X = Ty('X')
    fby, wait = FollowedBy(X), Swap(X, X.d).feedback()
    zero, one = Box('0', Ty(), X), Box('1', Ty(), X)
    copy, plus = Copy(X), Box('+', X @ X, X)


    @Diagram.feedback
    @Diagram.from_callable(X.d, X @ X)
    def fib(x):
        y = fby(zero.head(), plus.d(fby.d(one.head.d(), wait.d(x)), x))
        return (y, y)

    fib_ = (
        copy.d >> one.head.d @ wait.d @ X.d
            >> fby.d @ X.d
            >> plus.d
            >> zero.head @ X.d
            >> fby >> copy).feedback()
    assert Equation(fib.arg, fib_.arg)

    F = Functor(
        ob_map={X: (int, )},
        ar_map={zero: lambda: 0,
            one: lambda: 1,
            plus: lambda x, y: x + y},
        cod=stream.Stream[python.Function])

    assert F(fib).unroll(9).now()[:10] == (0, 1, 1, 2, 3, 5, 8, 13, 21, 34)


def test_Permutation_delay():
    x, y, z = map(Ty, "xyz")
    perm = Permutation(x @ y @ z, [2, 0, 1])
    assert perm.delay() == Permutation((x @ y @ z).delay(), [2, 0, 1])
    assert perm.delay(2) == perm.delay().delay()
    assert (perm >> Swap(z, x) @ y).delay()\
        == perm.delay() >> Swap(z, x).delay() @ y.delay()


def test_discard_is_a_feedback_diagram():
    x = Ty('x')
    discard = Diagram.copy(x, n=0)
    assert isinstance(discard, Diagram) and isinstance(discard, Discard)
    assert (discard >> Diagram.id(Ty())).boxes == [discard]
    assert discard.delay() == Discard(x.delay())


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
