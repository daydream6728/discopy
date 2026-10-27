# -*- coding: utf-8 -*-

import importlib
from collections import Counter
from random import Random

import pytest

pytest.importorskip("cvxpy")
pytest.importorskip("sympy")

from discopy import monoidal
from discopy.boltzmann import compile, shapes
from discopy.cat import Arrow
from discopy.grammar import categorial

MODULES = (
    "monoidal", "braided", "balanced", "symmetric", "feedback", "rigid",
    "pivotal", "ribbon", "compact", "markov", "comarkov", "closed",
    "biclosed", "frobenius")
""" The modules of free diagrams whose sampling diagrams are drawn. """


def categories():
    """ Each free category whose sampling diagram is drawn, by name. """
    yield "cat.Arrow", Arrow, None
    yield "monoidal.Ty", monoidal.Ty, None
    for name in MODULES:
        module = importlib.import_module(f"discopy.{name}")
        yield f"{name}.Diagram", module.Diagram, (1, 1)
    yield "grammar.categorial.Diagram", categorial.Diagram, (1, 1)


@pytest.mark.parametrize(
    "name, category, shape", list(categories()),
    ids=[name for name, *_ in categories()])
def test_sampling_diagram(name, category, shape):
    """
    The sampling diagram of each free category, of the morphisms with one
    input and one output: its terms are the productions of that sort, whose
    product of data is the right-hand side of its equation.
    """
    spec = category.boltzmann()
    sort = spec.root if shape is None else spec.shapes[shape]
    equation = spec.diagrams(sort)
    assert len(equation.terms) - 1 == len([
        production for production in spec.productions
        if production.cod == sort])
    equation.draw(
        doctest=f"docs/_static/boltzmann/{name.replace('.', '-')}.svg",
        figsize=(2.2 * len(equation.terms), 3), fontsize=9)


def test_system_of_arrows():
    """ The arrows of a category are the binary trees with two leaves. """
    spec = compile(Arrow)
    T, = spec.symbols.values()
    z, u_box, u_ax, u_cut = spec.parameters
    assert spec.system() == {T: z * u_box + z * u_ax + z * u_cut * T ** 2}


@pytest.mark.parametrize("module", ["monoidal", "symmetric", "compact"])
def test_tune(module):
    """ Tuning hits the expected size and applications it is asked for. """
    spec = importlib.import_module(f"discopy.{module}").Diagram.boltzmann()
    params = spec.tune(size=6, cut=2)
    assert abs(spec.expectation(params) - 6) < 1e-3
    assert abs(spec.expectation(params, "cut") - 2) < 1e-3


def test_sample_is_boltzmann():
    """
    The derivations of arrows are drawn with the probability of their
    shape: a single node with probability ``2z / T``.
    """
    spec = compile(Arrow)
    params = spec.tune(size=3)
    value, = spec.oracle(params)
    random = Random(0)
    trees = [spec.sample(random, params) for _ in range(20_000)]
    single = Counter(not tree.branches for tree in trees)[True] / len(trees)
    assert abs(single - 2 * params[spec.size] / value) < 0.02


def test_max_size():
    """ A derivation past the size bound is abandoned. """
    spec = compile(Arrow)
    params = spec.tune(size=8)
    random = Random(0)
    assert any(spec.sample(random, params, max_size=1) is None
               for _ in range(100))


def test_cups_are_drawn():
    """ A rigid diagram from x to x has cups in some draws, in blocks. """
    from hypothesis import given, settings, strategies as st
    from discopy import rigid
    x, seen = rigid.Ty('x'), []

    @settings(max_examples=50, deadline=None, database=None)
    @given(st.data())
    def check(data):
        diagram = data.draw(rigid.Diagram.strategy(dom=x, cod=x))
        seen.extend(type(box).__name__ for box in diagram.boxes)

    check()
    assert "Cup" in seen


def test_shapes():
    """ A category with no tensor has a single sort, as does a monoid. """
    assert len(compile(Arrow).sorts) == 1
    assert len(compile(monoidal.Ty).sorts) == 1
    assert shapes(monoidal.Diagram, 1) == (monoidal.Ty(), monoidal.Ty('a'))


@pytest.mark.parametrize("module", MODULES)
def test_boundary(module):
    """ A term is drawn with the boundary it is asked for. """
    from hypothesis import given, settings, strategies as st
    category = importlib.import_module(f"discopy.{module}")
    x, y = category.Ty('x'), category.Ty('y')

    @settings(max_examples=10, deadline=None)
    @given(st.data())
    def check(data):
        term = data.draw(category.Diagram.strategy(dom=x @ y, cod=y))
        assert (term.dom, term.cod) == (x @ y, y)

    check()
