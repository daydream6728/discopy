# -*- coding: utf-8 -*-

import inspect
import sys
from functools import cache

import pytest
from pytest import raises

from discopy.cat import *
from discopy.utils import AxiomError


def test_main():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    f, g, h = Box('f', x, y), Box('g', y, z), Box('h', z, x)
    assert Id(x) >> f == f == f >> Id(y)
    assert (f >> g).dom == f.dom and (f >> g).cod == g.cod
    assert f >> g >> h == f >> (g >> h)
    F = Functor(ob_map={x: y, y: z, z: x}, ar_map={f: g, g: h})
    assert F(Id(x)) == Id(F(x))
    assert F(f >> g) == F(f) >> F(g)


def test_Ob():
    assert Ob('x') == Ob('x') and Ob('x') != Ob('y')


def test_Ob_init():
    assert (Ob('x'), Ob('Alice')) == (Ob('x'), Ob('Alice'))


def test_Ob_name():
    assert Ob('x').name == 'x'


def test_Ob_repr():
    assert repr(Ob('x')) == "cat.Ob('x')"


def test_Ob_str():
    assert str(Ob('x')) == 'x'


def test_Ob_eq():
    x, x1, y = Ob('x'), Ob('x'), Ob('y')
    assert x == x1 and x != y and x != 'x'
    assert 'x' != Ob('x')


def test_Ob_hash():
    assert {Ob('x'): 42}[Ob('x')] == 42


def test_Arrow():
    x, y, z, w = Ob('x'), Ob('y'), Ob('z'), Ob('w')
    f, g, h = Box('f', x, y), Box('g', y, z), Box('h', z, w)
    assert f >> g >> h == Arrow((f, g, h), x, w)


def test_Arrow_init():
    with raises(TypeError) as err:
        Arrow((), 1, Ob('x'))
    with raises(TypeError) as err:
        Arrow((), Ob('x'), 1)
    with raises(TypeError) as err:
        Arrow((Ob('x'), ), Ob('x'), Ob('x'))


def test_Arrow_len():
    assert len(Arrow((), Ob('x'), Ob('x'))) == 0


def test_Arrow_getitem():
    f, g = Box('f', Ob('x'), Ob('y')), Box('g', Ob('y'), Ob('z'))
    arrow = f >> g >> g.dagger() >> f.dagger()\
        >> f >> g >> g.dagger() >> f.dagger()
    with raises(TypeError):
        arrow["Alice"]
    with raises(IndexError):
        arrow[9]
    assert arrow[:] == arrow
    assert arrow[::-1] == arrow.dagger()
    assert arrow[:0] == arrow[:-8] == arrow[-9:-9] == Id(arrow.dom)
    # Non-unit steps return the corresponding sub-path (daggered when the
    # step is negative), raising only when the result is not composable.
    h = Box('h', Ob('x'), Ob('x'))
    loop = h >> h >> h
    assert loop[::2] == h >> h
    assert loop[::-2] == (h >> h).dagger()
    with raises(AxiomError):
        arrow[::2]
    with raises(AxiomError):
        arrow[::-2]
    for depth, box in enumerate(arrow):
        assert arrow[depth] == box
        assert arrow[-depth] == arrow.inside[-depth]
        assert arrow[depth:depth] == Id(box.dom)
        assert arrow[depth:] == Id(box.dom).then(*arrow.inside[depth:])
        assert arrow[:depth] == Id(arrow.dom).then(
            *arrow.inside[:depth])
        assert arrow[depth: depth + 2] == Id(box.dom).then(
            *arrow.inside[depth: depth + 2])


def test_Arrow_repr():
    assert repr(Arrow((), Ob('x'), Ob('x'))) == "cat.Arrow.id(cat.Ob('x'))"
    inside = (Box('f', Ob('x'), Ob('y')), Box('g', Ob('y'), Ob('z')))
    assert repr(Arrow(inside, Ob('x'), Ob('z')))\
        == "cat.Arrow(inside=(cat.Box('f', cat.Ob('x'), cat.Ob('y')), "\
           "cat.Box('g', cat.Ob('y'), cat.Ob('z'))), dom=cat.Ob('x'), "\
           "cod=cat.Ob('z'))"


def test_Arrow_str():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    f, g = Box('f', x, y), Box('g', y, z)
    assert str(Arrow((), x, x)) == "Id(x)"
    assert str(Arrow((f, ), x, y)) == "f"
    assert str(Arrow((f, g), x, z)) == "f >> g"


def test_Arrow_eq():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    f, g = Box('f', x, y), Box('g', y, z)
    assert f >> g == Arrow((f, g), x, z)


def test_Arrow_hash():
    assert {Id(Ob('x')): 42}[Id(Ob('x'))] == 42


def test_Arrow_then():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    f, g = Box('f', x, y), Box('g', y, z)
    assert f.then(g) == f >> g == g << f
    with raises(TypeError) as err:
        f >> x


def test_Arrow_dagger():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    f, g = Box('f', x, y), Box('g', y, z)
    h = Arrow((f, g), x, z)
    assert h.dagger() == g.dagger() >> f.dagger()
    assert h.dagger().dagger() == h
    assert isinstance(h, DaggerCategory)
    assert not issubclass(FreeCategory, DaggerCategory)
    assert not issubclass(Functor, DaggerCategory)


def test_Id_init():
    idx = Id(Ob('x'))
    assert idx >> idx == idx
    assert idx.dagger() == idx


def test_Id_repr():
    assert repr(Id(Ob('x'))) == "cat.Arrow.id(cat.Ob('x'))"


def test_Id_str():
    x = Ob('x')
    assert str(Id(x)) == "Id(x)"


def test_AxiomError():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    f, g = Box('f', x, y), Box('g', y, z)
    with raises(AxiomError) as err:
        Arrow((g, ), x, y)
    with raises(AxiomError) as err:
        Arrow((f, ), x, z)
    with raises(AxiomError) as err:
        g >> f


def test_Box():
    f = Box('f', Ob('x'), Ob('y'), data=[42, {0: 1}, lambda x: x])
    assert f >> Id(Ob('y')) == f == Id(Ob('x')) >> f


def test_Box_dagger():
    f = Box('f', Ob('x'), Ob('y'), data=[42, {0: 1}])
    assert f.dom == f.dagger().cod and f.cod == f.dagger().dom
    assert f == f.dagger().dagger()


def test_Bubble_dagger():
    f = Box('f', Ob('x'), Ob('y'))
    b = f.bubble(data=42)
    assert b.dagger().data == 42 and b.dagger().is_dagger
    assert b.dagger().dagger() == b


def test_Box_repr():
    f = Box('f', Ob('x'), Ob('y'), data=42)
    assert repr(f) == "cat.Box('f', cat.Ob('x'), cat.Ob('y'), data=42)"
    assert repr(f.dagger())\
        == "cat.Box('f', cat.Ob('x'), cat.Ob('y'), data=42).dagger()"


def test_Box_str():
    f = Box('f', Ob('x'), Ob('y'), data=42)
    assert str(f) == "f"
    assert str(f.dagger()) == "f[::-1]"


def test_Box_hash():
    assert {Box('f', Ob('x'), Ob('y')): 42}[Box('f', Ob('x'), Ob('y'))] == 42


def test_Box_eq():
    f = Box('f', Ob('x'), Ob('y'), data=[42, {0: 1}])
    assert f == Arrow((f, ), Ob('x'), Ob('y')) and f != Ob('x')


def test_Box_generator_hash():
    """
    A box and the length-one arrow made of that box are equal, so they must
    also hash equally, see https://github.com/discopy/discopy/pull/387
    """
    x, y = Ob('x'), Ob('y')
    f = Box('f', x, y)
    assert f.is_generator and f.generator is f
    arrow = Id(x) >> f
    assert arrow.is_generator and arrow.generator == f
    assert f == arrow and hash(f) == hash(arrow)
    assert {f: 42}[arrow] == 42 and {arrow: 42}[f] == 42
    # A genuine arrow of length two is not a generator.
    g = Box('g', y, x)
    assert not (f >> g).is_generator and (f >> g).generator is None


def test_Sum_generator_hash():
    """
    A singleton ``Sum`` equals its unique term, so it must hash like it too,
    see https://github.com/discopy/discopy/pull/387
    """
    x, y = Ob('x'), Ob('y')
    f = Box('f', x, y)
    singleton = Sum((f, ), x, y)
    assert singleton == f and hash(singleton) == hash(f)
    assert {f: 42}[singleton] == 42


def test_Functor():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    f, g = Box('f', x, y), Box('g', y, z)
    F = Functor({x: y, y: x, z: z}, {f: f.dagger(), g: f >> g})
    assert F((f >> g).dagger()) == F(f >> g).dagger()
    assert F(Id(Ob('x'))) == Id(Ob('y'))


def test_Functor_eq():
    x, y = Ob('x'), Ob('y')
    assert Functor({x: y, y: x}, {}) == Functor({y: x, x: y}, {})
    F, G = Functor({}, {}), Functor({}, {}, dom=Box)
    assert F != G
    assert repr(G) == "cat.Functor(ob_map={}, ar_map={}, dom=cat.Box)"


def test_Functor_repr():
    assert repr(Functor({}, {})) == "cat.Functor(ob_map={}, ar_map={})"


def test_Functor_call():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    f, g = Box('f', x, y), Box('g', y, z)
    F = Functor({x: y, y: x, z: z}, {f: f.dagger(), g: f >> g})
    with raises(TypeError) as err:
        F(F)
    assert F(x) == y
    assert F(f) == f.dagger()
    assert F(f.dagger()) == f
    assert F(g) == f >> g
    assert F(f >> g) == f.dagger() >> f >> g


def test_Transformation():
    x, y = Ob('x'), Ob('y')
    f = Box('f', x, y)
    F, G = Functor.id(), Functor({x: y, y: x}, {})
    alpha = Transformation({x: f, y: f[::-1]}, F, G)
    assert alpha(x) == f and alpha(y) == f[::-1]
    assert alpha.dom == F and alpha.cod == G


def test_Transformation_id():
    x, y = Ob('x'), Ob('y')
    F = Functor({x: y, y: x}, {})
    idF = Transformation.id(F)
    assert idF.dom == idF.cod == F
    assert idF(x) == Id(F(x)) == Id(y)


def test_Transformation_then():
    x, y = Ob('x'), Ob('y')
    f = Box('f', x, y)
    F, G = Functor.id(), Functor({x: y, y: x}, {})
    alpha = Transformation({x: f, y: f[::-1]}, F, G)
    beta = Transformation.id(G)
    assert (alpha >> beta)(x) == alpha(x) >> beta(x)
    assert (alpha >> beta).dom == F and (alpha >> beta).cod == G


def test_Transformation_eq():
    x, y = Ob('x'), Ob('y')
    f = Box('f', x, y)
    F, G = Functor.id(), Functor({x: y, y: x}, {})
    assert Transformation({x: f, y: f[::-1]}, F, G)\
        == Transformation({x: f, y: f[::-1]}, F, G)
    assert Transformation({x: f, y: f[::-1]}, F, G) != F


def test_Transformation_repr():
    F = Functor.id()
    assert "Transformation" in repr(Transformation.id(F))


def test_Transformation_errors():
    x, y = Ob('x'), Ob('y')
    F = Functor.id()
    H = Functor({x: y, y: x}, {})
    # Vertical composition requires self.cod == other.dom.
    with raises(AxiomError):
        Transformation.id(F) >> Transformation.id(H)
    # then only composes with another Transformation.
    with raises(TypeError):
        Transformation.id(F) >> F
    # A component must be an arrow from dom(x) to cod(x).
    f = Box('f', x, y)
    with raises(AxiomError):
        Transformation({x: f, y: f[::-1]}, F, F)(x)


def test_total_ordering():
    x, y, z = Ob('x'), Ob('y'), Ob('z')
    assert sorted([z, y, x]) == [x, y, z]
    f, g = Box('f', x, y), Box('g', y, z)
    assert f < g


def test_Bubble():
    f = Box('f', Ob('x'), Ob('y'))
    assert repr((f).bubble())\
        == "cat.Bubble(cat.Box('f', cat.Ob('x'), cat.Ob('y')))"
    assert str(f.bubble()) == "(f).bubble()"
    named = f.bubble(name="N", method="m")
    assert repr(named) == "cat.Bubble(cat.Box('f', cat.Ob('x'), cat.Ob('y')),"\
        " name='N', method='m')"
    assert eval(repr(named), {"cat": __import__("discopy").cat}) == named
    assert Functor.id()(f.bubble(name="N")) == f.bubble(name="N")
    image = Functor.id()(f.bubble(data=42, is_dagger=True))
    assert (image.data, image.is_dagger) == (42, True)
    empty = Bubble(dom=Ob('x'), cod=Ob('y'))
    assert Functor.id()(empty) == empty


def test_Box_call():
    f = Box('f', Ob('x'), Ob('y'))
    with raises(TypeError):
        f(42)


def test_from_tree():
    f = Box('f', Ob('x'), Ob('y'), data=[42, {0: 1}])
    d = (f >> f[::-1].bubble()) + Id(Ob('x'))
    assert from_tree(d.to_tree()) == d


def test_sum_lambdify():
    pytest.importorskip("sympy")
    from sympy.abc import phi
    f = Box('f', Ob('x'), Ob('y'), data=[phi])
    g = Box('g', Ob('x'), Ob('y'), data=[phi])

    assert (f + g).free_symbols == {phi}
    assert (f + g).lambdify(phi)(1) == f.lambdify(phi)(1) + g.lambdify(phi)(1)

    empty_sum = Sum((), Ob('x'), Ob('y'))
    assert empty_sum.lambdify(phi)(123) == empty_sum

    assert empty_sum.subs(phi, 0) == empty_sum


def test_Bubble_subs_lambdify():
    pytest.importorskip("sympy")
    from sympy.abc import phi, psi
    f = Box('f', Ob('x'), Ob('x'), data=phi)
    bubble = Bubble(f, f, name="b", method="m", data=phi)
    expected = Bubble(f.subs(phi, 1), f.subs(phi, 1),
                      name="b", method="m", data=1)
    assert bubble.subs(phi, 1) == bubble.lambdify(phi)(1) == expected
    assert bubble.subs(phi, 1).data == bubble.lambdify(phi)(1).data == 1
    assert bubble.subs(psi, 1) == bubble.lambdify(psi)(1) == bubble


def test_subs_forms_and_data():
    pytest.importorskip("sympy")
    import numpy as np
    from sympy.abc import phi, psi
    x, y = Ob('x'), Ob('y')
    f = Box('f', x, y, data=phi + psi)
    expected = Box('f', x, y, data=3)
    assert f.subs(phi, 1).data == f.subs([(phi, 1)]).data\
        == f.subs((phi, 1)).data == psi + 1
    for args in [([(phi, 1), (psi, 2)], ), ({phi: 1, psi: 2}, ),
                 ((phi, 1), (psi, 2))]:
        assert f.subs(*args) == expected
    g = Box('g', x, y, data=["phi", {"phase": phi}])
    assert g.free_symbols == {phi}
    assert Box('h', x, y, data="h").free_symbols == set()
    assert g.subs(phi, 1).data == g.lambdify(phi)(1).data\
        == ["phi", {"phase": 1}]
    h = Box('h', x, y, data=np.array([[phi, 1], [psi, 2]], dtype=object))
    assert np.array_equal(h.subs(psi, 4).subs(phi, 3).data, [[3, 1], [4, 2]])
    import sympy
    for data in (h.data, sympy.Matrix(h.data), sympy.Array(h.data)):
        h = Box('h', x, y, data=data)
        for result in (h.subs([(phi, 3), (psi, 4)]), h.lambdify(phi, psi)(3, 4)):
            assert np.array_equal(np.array(result.data), [[3, 1], [4, 2]])
    empty = Box('e', x, y, data=np.zeros((0, 3))).subs(phi, 1).data
    assert empty.shape == (0, 3)
    lam = sympy.Symbol("lambda")
    for data in (sympy.sin(phi) + sympy.sin(psi), phi + lam):
        assert Box('p', x, y, data=data).subs(phi, 1).data == data.subs(phi, 1)
    from discopy.utils import rsubs
    data = [sympy.sin(phi) + psi, phi, sympy.Matrix([[sympy.sin(phi)]])]
    assert rsubs(data, sympy.sin(phi), 0) == rsubs(data, {sympy.sin(phi): 0})\
        == [psi, phi, sympy.Matrix([[0]])]


def test_Sum():
    x, y, z = map(Ob, "xyz")
    f = Box('f', x, y)
    g = Box('g', y, z)
    with raises(ValueError):
        Sum(())
    with raises(AxiomError):
        Sum((), x, y) + Sum((), y, z)
    with raises(AxiomError):
        Sum((f, ), y, z)
    with raises(AxiomError):
        Sum((f, g))
    assert hash(Sum((), x, y)) == hash(Sum((), x, y))
    assert repr(Sum((), x, y))\
        == "cat.Sum(terms=(), dom=cat.Ob('x'), cod=cat.Ob('y'))"
    lazy = Sum((f, f))
    assert "name" not in vars(lazy) and lazy.name == repr(lazy)\
        == f"cat.Sum(terms=({f!r}, {f!r}))"
    assert list(Sum((f, ), x, y)) == [f]
    assert len(Sum((), x, y)) == 0
    assert Sum((), x, x).then(f, g) == Sum((), x, z)
    assert Sum((), x, y).dagger() == Sum((), y, x)


def test_Functor_then_left_unit():
    """
    Composition is unital only on the left up to equality of functors
    (#648): the identity functor is a pair of functions, so composing it on
    the left of a functor given by dictionaries yields a pair of functions
    that acts the same but compares unequal.
    """
    x, y = Ob('x'), Ob('y')
    F = Functor({x: y, y: x}, {})
    assert F >> Functor.id() == F
    assert Functor.id() >> F != F
    assert (Functor.id() >> F)(x) == F(x)


def test_Bubble_no_common_boundary():
    x, y = Ob('x'), Ob('y')
    f, g = Box('f', x, x), Box('g', y, x)
    with raises(ValueError, match="needs a dom given"):
        Bubble(f, g)
    with raises(ValueError, match="needs a cod given"):
        Bubble(f, g[::-1], dom=x)
    assert Bubble(f, g, dom=x).cod == x
    with raises(ValueError, match=r"they have \[\]"):
        Bubble()


ABSTRACT = ("Timed", "ControlledRotation", "BinaryTerm", "Parametrized")


@cache
def box_classes():
    """ Every class of box that the package defines, see #169. """
    import importlib
    import pkgutil
    import discopy
    classes = {}
    for info in pkgutil.walk_packages(discopy.__path__, "discopy."):
        try:
            module = importlib.import_module(info.name)
        except ImportError:  # it needs an extra, see test/plugin.py
            continue
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, Box)\
                    and value.__module__ == info.name:
                classes[value] = None
    return list(classes)


@cache
def examples():
    """
    A builder of boxes for each constructor of the package, from a class, two
    types of its category and a value for the data.
    """
    from discopy import (
        balanced, biclosed, braided, closed, comarkov, ehypergraph, feedback,
        frobenius, markov, monoidal, pivotal, ribbon, rigid, symmetric,
        tensor)
    from discopy.grammar import categorial as cg, cfg, pregroup, thue
    from discopy.neural import network
    from discopy.quantum import circuit, gates, zx

    def box(c, x, y, v):
        return c.ar.box_factory("f", x, y, data=v)

    def term(c, x, y):
        constant, variable = c.ob.constant_factory, c.ob.variable_factory
        return constant("f", x << y), constant("a", y), variable("v", y)

    def abstraction(c, x, y, _):
        f, _, v = term(c, x, y)
        return c(v, f(v))

    builders = {
        (Box, ): lambda c, x, y, v: c("f", x, y, data=v, is_dagger=True),
        (Sum, markov.Sum): lambda c, x, y, v: c((box(c, x, y, v), )),
        (Bubble, ): lambda c, x, y, v: c(box(c, x, y, v), dom=y, data=v),
        (monoidal.Box, network.Box): lambda c, x, y, v: c("f", x, y, data=v),
        (monoidal.Bubble, ): lambda c, x, y, v: c(
            box(c, x, y, v), name="b", drawing_name="B"),
        (monoidal.Layer, ): lambda c, x, y, v: c(
            x, sys.modules[c.__module__].Box("f", x, y, data=v), y),
        (braided.Braid, balanced.DualRailBraid, ribbon.DualRailCup,
         ribbon.DualRailCap): lambda c, x, y, v: c(x, y, is_dagger=True),
        (balanced.Twist, balanced.DualRailTwist):
            lambda c, x, y, v: c(x, is_dagger=True),
        (symmetric.Swap, ): lambda c, x, y, v: c(x, y),
        (symmetric.Permutation, ): lambda c, x, y, v: c(x @ y @ x, [2, 0, 1]),
        (feedback.Box, ): lambda c, x, y, v: c("f", x, y, data=v).delay(),
        (feedback.Feedback, ): lambda c, x, y, v: c(
            box(c, x @ y.delay(), x @ y, v)),
        (feedback.Trace, ): lambda c, x, y, v: c(
            box(c, y @ x, y @ x, v), left=True),
        (feedback.Head, feedback.Tail):
            lambda c, x, y, v: c(box(c, x, y, v), 1),
        (feedback.FollowedBy, ): lambda c, x, y, v: c(x, True, 1),
        (markov.Box, ): lambda c, x, y, v: c(
            "f", x, y, data=v, is_deterministic=False).delay(),
        (markov.Copy, comarkov.Merge): lambda c, x, y, v: c(x, 3),
        (markov.Discard, comarkov.Noise, gates.Discard, gates.MixedState,
         cfg.Id): lambda c, x, y, v: c(x),
        (markov.Function, comarkov.Cofunction):
            lambda c, x, y, v: c(x @ y, [1, 0, 0]),
        (rigid.Box, ): lambda c, x, y, v: c("f", x, y, data=v).r,
        (rigid.Cup, frobenius.Cup): lambda c, x, y, v: c(x, x.r),
        (rigid.Cap, frobenius.Cap): lambda c, x, y, v: c(x, x.l),
        (pivotal.Box, ): lambda c, x, y, v: c("f", x, y, data=v).delay().r,
        (pregroup.Box, ): lambda c, x, y, v: c(
            "f", x, y, data=v, is_deterministic=False).r,
        (tensor.Box, ): lambda c, x, y, v: c("f", x, y, [v] + [0] * 5),
        (frobenius.Spider, ): lambda c, x, y, v: c(1, 2, x, data=v),
        (frobenius.Cospan, ): lambda c, x, y, v: c(x @ y, [0, 0, 1], [1]),
        (biclosed.Eval, biclosed.Coeval): lambda c, x, y, v: c(x << y),
        (closed.Eval, closed.Coeval):
            lambda c, x, y, v: c(x << y, time_step=1),
        (biclosed.Curry, closed.Curry):
            lambda c, x, y, v: c(box(c, x @ y, x, v), 1, False),
        (biclosed.Constant, ): lambda c, x, y, v: c("c", x, data=v),
        (closed.Constant, cg.Constant, biclosed.Variable, closed.Variable):
            lambda c, x, y, v: c("c", x),
        (biclosed.Application, closed.Application, cg.FA):
            lambda c, x, y, v: c(*term(c, x, y)[:2]),
        (biclosed.Abstraction, closed.Abstraction, cg.Abstraction):
            abstraction,
        (closed.Pack, closed.Unpack): lambda c, x, y, v: c(x * y, 1),
        (closed.Tuple, ): lambda c, x, y, v: c(*term(c, x, y)[1:]),
        (closed.Projection, ): lambda c, x, y, v: c(
            closed.Tuple(*term(closed.Box, x, y)[1:]), 1),
        (closed.Let, ): lambda c, x, y, v: c(
            closed.Tuple(*term(closed.Box, x, y)[1:2]),
            [closed.Variable("u", y)], closed.Variable("u", y)),
        (cg.BA, ): lambda c, x, y, v: c(cg.Constant("a", y), cg.Constant(
            "f", y >> x)),
        (cg.FTR, cg.BTR): lambda c, x, y, v: c(y, term(c, x, y)[1]),
        (cg.TypeRaising, ): lambda c, x, y, v: c(
            y, term(c, x, y)[1], y << (x >> y)),
        (cg.FC, ): lambda c, x, y, v: c(
            cg.Constant("f", x << y), cg.Constant("g", y << x)),
        (cg.BC, ): lambda c, x, y, v: c(
            cg.Constant("f", x >> y), cg.Constant("g", y >> x)),
        (cg.FX, cg.BX): lambda c, x, y, v: c(
            cg.Constant("f", x << y), cg.Constant("g", x >> y)),
        (cg.ForwardCrossedComposition, ):
            lambda c, x, y, v: c(x << y, x >> y),
        (cg.BackwardCrossedComposition, ):
            lambda c, x, y, v: c(y << x, y >> x),
        (thue.Rule, ): lambda c, x, y, v: c(x @ y, x, "r", data=v),
        (thue.Word, ): lambda c, x, y, v: c("w", x @ y, y, data=v),
        (cfg.Rule, ): lambda c, x, y, v: c(x @ y, x, "r"),
        (cfg.Word, ): lambda c, x, y, v: c("w", x, y),
        (pregroup.Word, ): lambda c, x, y, v: c("w", x @ y, data=v),
        (tensor.Bubble, ): lambda c, x, y, v: c(
            box(c, x, x, [v, 0, 0, 1]), func=abs, drawing_name="B"),
        (ehypergraph.Join, ):
            lambda c, x, y, v: c(box(c, x, y, v), box(c, x, y, v)),
        (circuit.Box, ): lambda c, x, y, v: c(
            "f", x, y, data=[v, 0, 0, 1], is_mixed=False),
        (gates.QuantumGate, ): lambda c, x, y, v: c("g", x, x, [v, 0, 0, 1]),
        (gates.Ket, gates.Bra): lambda c, x, y, v: c(1, 0, time_step=1),
        (gates.Digits, ): lambda c, x, y, v: c(
            1, 2, dim=3, is_dagger=True, time_step=1),
        (gates.Measure, gates.Encode):
            lambda c, x, y, v: c(2, False, True, 1),
        (gates.Copy, gates.Match): lambda c, x, y, v: c(1),
        (gates.Controlled, ): lambda c, x, y, v: c(gates.Rz(v), -2),
        (gates.ControlledRotation, ): lambda c, x, y, v: c(v, -2, 1),
        (gates.Rotation, ): lambda c, x, y, v: c(v, 1, 1),
        (gates.Scalar, ): lambda c, x, y, v: c(v, "s", True, 1),
        (gates.MixedScalar, ): lambda c, x, y, v: c(v, 1),
        (gates.Sqrt, ): lambda c, x, y, v: c(v, False, 1),
        (zx.Spider, ): lambda c, x, y, v: c(1, 2, v),
        (zx.Scalar, ): lambda c, x, y, v: c(v),
    }
    return {cls: build for classes, build in builders.items()
            for cls in classes}


def example(cls, value):
    """ The box :func:`examples` builds of a class, from its constructor. """
    from discopy import monoidal, tensor
    from discopy.neural.network import Dims
    from discopy.quantum import circuit
    from discopy.rigid import Nat
    if inspect.isabstract(cls) or cls.__name__ in ABSTRACT:
        return None
    owner = next(c for c in cls.__mro__ if "__init__" in vars(c))
    builders = examples()
    base = next(c for c in cls.__mro__ if c in builders)
    assert issubclass(base, owner), f"{owner} needs an example"
    ob = sys.modules[cls.__module__].Ty\
        if issubclass(cls, monoidal.Layer) else cls.ob
    x, y = (tensor.Dim(2), tensor.Dim(3)) if issubclass(cls, tensor.Box)\
        else (Dims(2), Dims(3)) if ob is Dims\
        else (Nat(1), Nat(1)) if ob is Nat else (ob('x'), ob('y'))
    if issubclass(cls, circuit.Box):
        x, y = circuit.qubit, circuit.qubit
    return builders[base](cls, x, y, value)


def holds(law, cls):
    """ Whether a law of #169 holds of the example of a class. """
    from discopy.utils import dumps, loads
    box = example(cls, 1)
    if law == "dagger":
        try:
            return box.dagger().dagger() == box
        except AxiomError:  # the box has no dagger
            return True
    if law == "rotation":
        return not hasattr(box, "rotate") or box.r.l == box == box.l.r
    if law == "rebuild":
        result, expected = box.rebuild(), box
    elif law == "subs":
        from sympy import S
        from sympy.abc import phi
        symbolic, expected = example(cls, phi), example(cls, S.One)
        for result in (symbolic.subs(phi, 1), symbolic.subs([(phi, 1)]),
                       symbolic.lambdify(phi)(1)):
            assert type(result) is type(expected) and result == expected
        return True
    else:
        result, expected = loads(dumps(box)), box
    return type(result) is type(expected) and result == expected


def expand(patterns: str) -> set[str]:
    """ The factory names a pattern means, e.g. ``{rigid,pivotal}.Cup``. """
    import itertools
    import re
    names = set()
    for pattern in patterns.split():
        parts = re.split(r"\{([^}]*)\}", pattern)
        options = [part.split(",") if i % 2 else [part]
                   for i, part in enumerate(parts)]
        names |= set(map("".join, itertools.product(*options)))
    return names


LEVELS = "{monoidal,feedback,symmetric,markov,comarkov,rigid,pivotal,compact,"\
    "frobenius}"
FEEDBACKS = "{feedback,balanced,symmetric,markov,comarkov,closed,pivotal,"\
    "ribbon,compact,frobenius,grammar.abstract,neural.network}"
PIVOTALS = "{pivotal,ribbon,compact,frobenius}"
SPIDERS = "{frobenius,tensor,grammar.pregroup}.Spider "\
    "quantum.zx.{Spider,X,Y,Z}"
TERMS = "{biclosed,closed,grammar.abstract,grammar.categorial}.{Constant,"\
    "Variable,Abstraction} {biclosed,closed,grammar.abstract}.Application "\
    "closed.{Tuple,Projection,Let} grammar.categorial.{FA,BA,TypeRaising,FTR,"\
    "BTR,FC,BC,FX,BX,ForwardCrossedComposition,BackwardCrossedComposition}"
BROKEN = {
    "rebuild": {
        LEVELS + ".Layer": "a layer keeps its *inside as boxes_or_types",
        "{markov,closed,grammar.abstract,neural.network}.{Copy,Discard} "
        "{comarkov,neural.network}.{Merge,Noise}": "it keeps neither x nor n",
        "{comarkov,neural.network}.Cofunction": "it keeps cofunc in an op",
        "frobenius.Cospan": "it keeps left and right as legs",
        SPIDERS: "it keeps neither n_legs_in nor n_legs_out",
        "closed.{Pack,Unpack}": "it keeps its type delayed",
    },
    "dagger": {
        TERMS: "a term has no stated dagger",
        FEEDBACKS + ".{Feedback,Head,Tail}": "it has no stated dagger",
        PIVOTALS + ".Trace": "its dagger is drawn with cups and caps",
    },
    "rotation": {
        PIVOTALS + ".{Feedback,Trace,Head,Tail,FollowedBy} "
        "{frobenius,tensor}.Bubble": "it has no stated rotation",
        "{tensor,quantum.circuit,quantum.zx}.Sum": "it rotates as a box",
        "ribbon.{DualRailCup,DualRailCap}": "its rotation drops is_dagger",
        "quantum.zx.Scalar": "it takes no dom, cod or z",
    },
    "subs": {
        SPIDERS: "it keeps neither n_legs_in nor n_legs_out",
        "grammar.categorial.{FC,BC,FX,BX}": "it has no data, see #321",
    },
    "tree": {
        "{balanced,ribbon}.{DualRailBraid,DualRailTwist} "
        "ribbon.{DualRailCup,DualRailCap} grammar.cfg.Id quantum.zx.Scalar":
        "it has no from_tree of its own",
        "quantum.gates.{CRx,CRz,CU1}": "its tree is that of a controlled gate",
        "grammar.categorial.TypeRaising": "its tree drops its cod",
        "neural.network.{Box,Feedback,Trace,Head,Tail}": "a module has none",
    },
}


@pytest.mark.parametrize("law", BROKEN)
def test_every_box(law):
    """
    The conformance test of #169: every class of box rebuilds from its
    fields, and so does its dagger, its rotations, its substitutions and its
    tree, but for the breakages each law lists with their reasons.
    """
    if law == "subs":
        pytest.importorskip("sympy")
    from discopy.utils import factory_name
    broken = set().union(*map(expand, BROKEN[law]))
    failures, checked = {}, set()
    for cls in box_classes():
        if example(cls, 1) is None:
            continue
        name = factory_name(cls)
        checked.add(name)
        try:
            if not holds(law, cls):
                failures[name] = "not equal"
        except Exception as error:  # pylint: disable=broad-except
            failures[name] = repr(error)
    unexpected = {k: v for k, v in failures.items() if k not in broken}
    fixed = (broken & checked) - set(failures)
    assert not unexpected and not fixed, (unexpected, fixed)
