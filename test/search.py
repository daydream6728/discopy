""" The rules and generators of a category, and the search by them. """


from typing import Annotated

from hypothesis import find
from hypothesis import strategies as st
from pytest import raises

from discopy import braided, rigid, traced
from discopy.abc import Category, ColouredMonoid
from discopy.monoidal import Box, Diagram, Ty
from discopy.pattern import C0, C1, Hom, Unit, declarations
from discopy.search import Generator, Rule, generator, rule, search
from discopy.utils import AxiomError


x, y = Ty("x"), Ty("y")


def test_rule():
    assert repr(Rule(Category.then.function)) == "Rule(then)"
    assert repr(Category.then) == "abc.Category.then"
    assert Diagram.then is not None and Diagram.rules["then"].category\
        is Diagram
    assert hash(Category.then) == hash(Category.then.bind(Category))
    assert Category.then.__isabstractmethod__
    assert Diagram.rules["then"].__doc__ == Category.then.__doc__
    with raises(TypeError):
        Rule(Category.then.function).scope
    with raises(TypeError):
        rule(classmethod(lambda cls: None))

    class Wrapped(Diagram):
        @rule
        def twice[A: C0](self: Annotated[C1, Hom[A, A]]
                         ) -> Annotated[C1, Hom[A, A]]:
            """ A rule declared and implemented in one place. """
            return self >> self

    f = Box("f", x, x)
    assert Wrapped.twice(f) == f >> f == Wrapped(f.inside, x, x).twice()
    assert list(Wrapped.rules) == ["then", "tensor", "twice"]
    assert str(Wrapped.rules["twice"])\
        == "twice: A: C0 | self: C1[A, A] ⊢ C1[A, A]"
    found = find(Wrapped.strategy(dom=x, cod=x, types=st.just(x)),
                 lambda value: len(value.boxes) == 2
                 and len(set(value.boxes)) == 1)
    assert found.boxes[0] == found.boxes[1]


def test_generator():
    @generator
    def wrong[A: C0](cls, f: Annotated[C1, Hom[A, A]]
                     ) -> Annotated[C1, Hom[A, A]]:
        ...
    with raises(TypeError):
        wrong.sequent
    assert type(declarations(rigid.Diagram, Generator)["cups"]) is Generator
    assert "cups" not in declarations(rigid.Diagram, Rule)
    assert rigid.Diagram.generators["cups"].category is rigid.Diagram
    assert str(braided.Diagram.generators["braid"]) == (
        "braid: X: Atom[C0], Y: Atom[C0] | left: X, right: Y"
        " ⊢ C1[X @ Y, Y @ X]")

    class Lying(Diagram):
        @classmethod
        @generator
        def wrong[A: ColouredMonoid](
                cls, dom: A) -> Annotated[C1, Hom[A, Unit[C0]]]:
            """ A generator whose conclusion lies. """
            return cls.id(dom)

    with raises(AxiomError):
        find(Lying.strategy(dom=x, cod=Ty()), lambda value: True)


def test_declarations():
    class Hidden(Diagram):
        unitality = None
        then = None

    assert "unitality" not in Hidden.axioms
    assert "then" in Hidden.rules
    assert list(declarations(Category, Generator)) == ["id"]


def test_search():
    strategy = search(Diagram, Box.strategy, dom=x, cod=y, max_depth=2)
    term = find(strategy, lambda value: len(value.boxes) == 3)
    assert (term.dom, term.cod) == (x, y)
    assert find(search(Diagram, Box.strategy, dom=x, cod=x, max_depth=0),
                lambda value: not value.boxes) == Diagram.id(x)
    assert find(search(Diagram, Box.strategy, max_depth=0),
                lambda value: not value.boxes).dom == find(
                    search(Diagram, Box.strategy, max_depth=0),
                    lambda value: not value.boxes).cod


def test_search_residual():
    """ The evaluation generator matches a goal by its residual. """
    from discopy.biclosed import Diagram, Eval, Ty
    a, b = Ty('a'), Ty('b')
    term = find(Diagram.strategy(dom=(a << b) @ b, cod=a, max_depth=0),
                lambda value: isinstance(value, Eval))
    assert term == Diagram.ev(a, b)


def test_search_trace():
    """ The trace rule builds around any diagram of the traced type. """
    a = traced.Ty('a')
    term = find(traced.Diagram.strategy(dom=a, cod=a),
                lambda value: any(
                    isinstance(box, traced.Trace) and len(box.arg.boxes) > 1
                    for box in value.boxes))
    assert (term.dom, term.cod) == (a, a)
