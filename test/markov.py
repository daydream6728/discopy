from __future__ import annotations
import warnings
from random import choice, seed

from pytest import raises, warns

from discopy.python import Function

from discopy.markov import *
from discopy import *
from discopy.utils import AxiomError


def test_Discard_has_no_copies():
    x = Ty('x')
    assert Copy(x, 0) == Discard(x) == Discard(x, 0)
    with raises(ValueError):
        Discard(x, 2)


def test_spider_factory():
    x = Ty('x')
    assert Diagram.spider_factory(1, 3, x) == Copy(x, 3)
    for n_legs_in, n_legs_out, phase in [(2, 2, None), (2, 1, None), (1, 2, .5)]:
        with raises(ValueError, match="only spiders of markov.Diagram"):
            Diagram.spider_factory(n_legs_in, n_legs_out, x, phase)


def test_Copy_dagger():
    """ A Markov category is not a dagger category, see #94 on next. """
    x = Ty('x')
    for box in (Copy(x), Copy(x, 3), Discard(x)):
        with raises(AxiomError, match="not a dagger category"):
            box.dagger()


def test_deprecated_merge():
    x = Ty('x')
    with warns(DeprecationWarning, match="use discopy.comarkov.Merge"):
        assert markov.Merge is comarkov.Merge
    with warns(DeprecationWarning, match="use discopy.comarkov.Diagram.merge"):
        assert Diagram.merge(x) == comarkov.Merge(x)
    with raises(AttributeError):
        markov.Codiagonal
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        frobenius.Diagram.merge(frobenius.Ty('x'))
        neural.network.Network.merge(neural.network.Dims(2))


def test_Discard():
    assert isinstance(Discard(Ty('x')), Discard)
    assert isinstance(Copy(Ty('x'), n=0), Discard)


def test_equations():
    x = Ty('x')
    copy, discard = Copy(x), Copy(x, 0)
    add, minus, zero = Box('+', x @ x, x), Box('-', x, x), Box('0', Ty(), x)

    add >> copy, copy @ copy >> x @ Swap(x, x) @ x >> add @ add
    add >> discard, discard @ discard
    zero >> discard, Diagram.id(Ty())
    copy >> minus @ x >> add, discard >> zero, copy >> x @ minus >> add

    Diagram.id(x)
    x @ zero >> x @ copy >> add @ x >> discard @ x
    x @ zero @ zero >> discard @ discard @ x
    discard >> zero


def test_neural_network():
    x = Ty('x')
    add = lambda n: Box('$+$', x ** n, x)
    ReLU = Box('$\\sigma$', x, x)
    weights = [Box('w{}'.format(i), x, x) for i in range(4)]
    bias = Box('b', Ty(), x)

    network = Diagram.copy(x @ x, 2)\
    >> Diagram.tensor(*weights) @ bias >> add(5) >> ReLU

    F = Functor(ob_map={x: int}, ar_map={
            add(5): lambda *xs: sum(xs),
            ReLU: lambda x: max(0, x),
            bias: lambda: -1, **{
                weight: lambda x, w=w: x * w
                for weight, w in zip(weights, range(4))}},
        cod=Function)

    assert F(network)(42, 43) == max(0, sum([42 * 0, 43 * 1, 42 * 2, 43 * 3, -1]))


def test_Permutation():
    x, y, z = map(Ty, "xyz")
    assert Diagram.permutation_factory is Permutation
    perm = Permutation(x @ y @ z, [2, 0, 1])
    assert isinstance(perm, Box) and perm.cod == z @ x @ y
    assert Equation(perm >> perm.dagger(), Id(x @ y @ z))
    assert isinstance(perm.inside[0], Layer)
    assert Box('f', x, y).inside[0].boxes_or_types == (Box('f', x, y), )
    assert type(perm.inside[0].boxes_and_types[1]) is Permutation
    assert Permutation(x @ y, [1, 0]) == Swap(x, y)
    assert issubclass(Swap, Permutation)
    assert Equation(perm, perm.to_swaps())


def test_copy_serialisation():
    from discopy.utils import dumps, loads
    x = Ty('x')
    for box in (Copy(x), Copy(x, 3), Discard(x)):
        assert loads(dumps(box)) == box
    assert loads(dumps(Copy(x) >> Discard(x) @ x)) == Copy(x) >> Discard(x) @ x
    assert repr(Copy(x, 3)) == "markov.Copy(feedback.Ty(feedback.Wire('x')), 3)"
    tree = dumps(comarkov.Merge(x, 3)).replace("comarkov.Merge", "markov.Merge")
    with warns(DeprecationWarning):
        assert loads(tree) == comarkov.Merge(x, 3)


def test_copy_factory():
    from discopy.utils import factory

    @factory
    class Recipe(Diagram):
        """ A subclass with its own copies. """

    class RecipeCopy(Copy, Recipe):
        """ The copy of an ingredient. """

    class RecipeDiscard(Discard, RecipeCopy):
        """ The discard of an ingredient. """

    Recipe.copy_factory, Recipe.discard_factory = RecipeCopy, RecipeDiscard
    x = Ty('x')
    assert isinstance(Recipe.copy(x).boxes[0], RecipeCopy)
    assert isinstance(RecipeCopy(x, 0), RecipeDiscard)
    with raises(AxiomError, match="Recipe is not a dagger category"):
        RecipeCopy(x).dagger()


def test_Copy_pickle():
    from pickle import dumps, loads
    x = Ty('x')
    for box in (Copy(x), Copy(x, 3), Discard(x)):
        assert loads(dumps(box)) == box


def test_hypergraph():
    x = Ty('x')
    f, g, h = Box('f', Ty(), x), Box('g', Ty(), x), Box('h', x, x)
    graph = (f @ g >> x @ Copy(x)).to_hypergraph()
    assert graph.offsets == (0, 1)
    assert graph.to_diagram() == Diagram(
        (Layer(f, g), Layer(x, Copy(x))), Ty(), x @ x @ x)
    diagram = f @ g >> Copy(x) @ x >> h @ x @ x
    assert diagram.to_hypergraph().offsets == (0, 1, None)
    for diagram in (diagram, f @ g >> Discard(x) @ x):
        assert Equation(diagram.to_hypergraph().to_diagram(), diagram)


def test_stream_Diagram_repr():
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


def test_Discard_delay():
    x = Ty('x')
    discard = Diagram.copy(x, n=0)
    assert isinstance(discard, Diagram) and isinstance(discard, Discard)
    assert (discard >> Diagram.id(Ty())).boxes == [discard]
    assert discard.delay() == Discard(x.delay())


def test_delayed_Copy_pickle():
    from pickle import dumps, loads
    x = Ty('x')
    for box in (Copy(x), Discard(x), Copy(x).delay(), Discard(x).delay()):
        assert loads(dumps(box)) == box
