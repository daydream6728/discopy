""" The delooping of a monoidal category as a two-category. """

from pytest import raises

from discopy import deloop, monoidal, symmetric
from discopy.abc import TwoCategory
from discopy.deloop import Cell, Deloop, Monoidal, Symmetric
from discopy.monoidal import Box, Ty
from discopy.utils import AxiomError


x, y = Ty('x'), Ty('y')
f, g = Box('f', x, y), Box('g', y, x)
a, b = Monoidal(f), Monoidal(g)


def test_sequents():
    assert str(TwoCategory.compose.sequent) == (
        "F: C0, G: C0, H: C0, K: C0"
        " | self: C1[F, G], other: C1[H, K] ⊢ C1[F >> H, G >> K]")
    assert str(TwoCategory.interchange.sequent) == (
        "F1: C0, F2: C0, F3: C0, G1: C0, G2: C0, G3: C0 | a: C1[F1, F2],"
        " b: C1[F2, F3], c: C1[G1, G2], d: C1[G2, G3]")
    assert list(Monoidal.rules) == ["id", "then", "compose"]


def test_cells():
    one = Monoidal.ob(x)
    assert one >> Monoidal.ob(y) == Monoidal.ob(x @ y)
    assert len(one) == 1 and (one >> one)[1:] == one
    with raises(NotImplementedError):
        Cell.strategy()


def test_deloop():
    assert a.dom == Monoidal.ob(x) and a.cod == Monoidal.ob(y)
    assert (a >> b).inside == f >> g
    assert a.compose(b).inside == f @ g
    assert Monoidal.id(a.dom).inside == monoidal.Diagram.id(x)
    with raises(TypeError):
        a >> Symmetric(symmetric.Box('f', x, y))
    with raises(AxiomError):
        b >> b
    with raises(NotImplementedError):
        Deloop.strategy()


def test_equation():
    """ The equations delegate to the category of the arrows inside. """
    equation = Monoidal.Equation(a.compose(b), a.compose(b))
    assert isinstance(equation, monoidal.Equation) and equation
    assert not Monoidal.Equation(a, a >> b >> a)


def test_axioms():
    assert Monoidal.interchange(a, b, a, b)
    assert Monoidal.compose_identity(a.dom, b.dom)
    assert Monoidal.compose_associativity(a, b, a)
    assert Monoidal.compose_dom_typing(a, b)
    assert Monoidal.compose_cod_typing(a, b)
    assert Monoidal.unitality(a) and Monoidal.associativity(a, b, a)
    assert Monoidal.interchange.params == {"boundary_connected": True}
    assert Symmetric.interchange.params == {}


def test_strategy():
    from hypothesis import find
    drawn = find(Monoidal.strategy(dom=a.dom), lambda _: True)
    assert isinstance(drawn, Monoidal) and drawn.dom == a.dom
