from pytest import raises

from discopy.frobenius import *


def test_Functor_call():
    x = Ty('x')
    cup, cap = Cup(x, x.r), Cap(x.r, x)
    box1, box2 = Box('box', x, x), Box('box', x @ x, x @ x)
    spider = Spider(0, 2, x)
    F = Functor(lambda x: x @ x, {box1: box2})
    assert F(cup) == Id(x) @ cup @ Id(x.r) >> cup
    assert F(cap) == Id(x.r) @ cap @ Id(x) << cap
    assert F(box1) == box2
    assert F(box1.l) == box2.l and F(box1.r) == box2.r
    assert F(spider) == spider @ spider >> Id(x) @ Swap(x, x) @ Id(x)
    with raises(TypeError):
        F(F)


def test_Box_hash():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)
    assert f == f @ Id()
    assert hash(f) == hash(f @ Id())
    assert hash(f) == hash(Id() @ f)
    assert f @ Id() in {f}
    assert {f: 42}[f @ Id()] == 42
    s = Spider(1, 2, x)
    assert hash(s) == hash(s @ Id())


def test_spider_adjoint():
    n = Ty('n')
    one = Box('one', Ty(), n)
    two = Box('two', Ty(), n)
    diagram = one @ two >> Spider(2, 1, n)

    assert diagram.r == diagram.l == Spider(1, 2, n) >> two.r @ n >> one.r


def test_spider_factory():
    a, b, c = map(Ty, 'abc')
    ts = [a, a @ b, a @ b @ c]
    for i in range(5):
        for j in range(5):
            for t in ts:
                s = Diagram.spiders(i, j, t)
                for k, ob in enumerate(t):
                    assert all(map(ob.__eq__, s.dom[k::len(t)]))
                    assert all(map(ob.__eq__, s.cod[k::len(t)]))


def test_spider_decomposition():
    n = Ty('n')

    assert Spider(0, 0, n).unfuse() == Spider(0, 1, n) >> Spider(1, 0, n)
    assert Spider(1, 0, n).unfuse() == Spider(1, 0, n)
    assert Spider(1, 1, n).unfuse() == Id(n)
    assert Spider(2, 1, n).unfuse() == Spider(2, 1, n)

    # 5 is the smallest number including both an even and odd decomposition
    assert Spider(5, 1, n).unfuse() == (Spider(2, 1, n) @ Spider(2, 1, n)
                                           @ Id(n) >> Spider(2, 1, n) @ Id(n)
                                           >> Spider(2, 1, n))


def test_Functor_spider_into_a_comonoid():
    """A codomain with no spiders still copies and merges."""
    from discopy import markov, python
    x = Ty('x')
    to_python = Functor({x: (int, )}, {}, cod=python.Function)
    assert to_python(Diagram.spiders(1, 3, x))(42) == (42, 42, 42)
    assert to_python(Diagram.spiders(1, 0, x))(42) == ()
    successor = python.Function(lambda a: a + 1, (int, ), (int, ))
    assert (to_python(Diagram.spiders(1, 1, x)) >> successor)(42) == 43
    y = markov.Ty('y')
    to_markov = Functor({x: y}, {}, cod=markov.Diagram)
    assert to_markov(Diagram.spiders(1, 3, x)) == markov.Diagram.copy(y, 3)
    assert to_markov(Diagram.spiders(3, 1, x)) == markov.Diagram.merge(y, 3)


def test_Functor_spider_without_a_comonoid():
    """What the codomain cannot supply is looked up like any other box."""
    from discopy import python
    x = Ty('x')
    spider = Diagram.spiders(2, 1, x)
    with raises(Exception):  # python.Function has copies but no merges
        Functor({x: (int, )}, {}, cod=python.Function)(spider)
    merge = python.Function(lambda a, b: a + b, (int, int), (int, ))
    assert Functor({x: (int, )}, {spider: merge},
                   cod=python.Function)(spider)(54, 46) == 100
