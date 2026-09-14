""" The sequent patterns, their matching and the search by rules. """

from hypothesis import find
from hypothesis import strategies as st
from pytest import raises

from discopy import braided, monoidal, rigid, traced
from discopy.abc import Category, MonoidalCategory
from discopy.axioms import Equation
from discopy.monoidal import Box, Diagram, Ty
from discopy.search import (
    C0, C1, Atom, Attr, Axiom, Call, Generator, Hom, Op, Rule, Sequent,
    Sort, Tensor, Unit, Var, axiom, declarations, generator, parse, read,
    rule, search)
from discopy.utils import AxiomError


x, y, z = map(Ty, "xyz")
A, B = Var("A", Sort()), Var("B", Sort())
M = Var("M", Sort(atomic=True))


def test_read():
    sorts = {"A": Sort(), "M": Sort(atomic=True)}
    assert read("A @ M", sorts) == Tensor((A, M))
    assert read("(A @ M) @ A", sorts) == Tensor((A, M, A))
    assert read("1", sorts) == Unit()
    assert read("M.r", sorts) == Attr(M, "r")
    assert read("M.delay(2)", sorts) == Call(M, "delay", (2, ))
    assert read("A << M", sorts) == Op("<<", A, M)
    assert read("C0", sorts) == Sort("C0")
    assert read("Atom[C0]", sorts) == Sort("C0", atomic=True)
    assert read("Self.dom.ob", sorts) == Sort("Self.dom.ob")
    assert read("Self.dom.ar[A, M]", sorts) == Hom(A, M, "Self.dom.ar")
    assert A @ M == Tensor((A, M)) and 1 @ A == Tensor((Unit(), A))
    assert (A << M) == Op("<<", A, M) and (1 >> A) == Op(">>", Unit(), A)
    assert M.delay(2) == Call(M, "delay", (2, )) and M.r == Attr(M, "r")
    assert Atom[Sort("C0")] == Sort("C0", atomic=True)
    with raises(TypeError):
        Atom[A]
    with raises(AttributeError):
        A.__wrapped__
    assert str(read("C1[A @ M.r, 1]", sorts)) == "C1[A @ M.r, 1]"
    with raises(TypeError):
        read("A ** 2", sorts)
    with raises(TypeError):
        read("C0 @ A", sorts)
    with raises(TypeError):
        read("C1[A]", sorts)


def test_parse():
    def then[A: C0, B: C0, C: C0](
            self: C1[A, B], other: C1[B, C]) -> C1[A, C]:
        ...
    sequent = parse(then)
    assert list(sequent.variables) == ["A", "B", "C"]
    assert list(sequent.premises) == ["self", "other"]
    assert str(sequent.conclusion) == "C1[A, C]"
    assert parse(then, conclusion=False).conclusion is None

    def law(cls, x: Atom[C0], n: int = 1, *args, **kwargs):
        ...
    assert list(parse(law, conclusion=False).premises) == ["x"]
    assert str(parse(lambda cls: None, conclusion=False)) == ""
    with raises(TypeError):
        parse(law)

    def unsorted[A: C1[A, A]](cls, f: A):
        ...
    with raises(TypeError):
        parse(unsorted, conclusion=False)


def test_match():
    assert list(A.match(None)) == [({}, ())]
    assert [s for s, _ in Tensor((M, A)).match(x @ y)] == [
        {"M": x, "A": y}]
    assert list(Tensor((M, M)).match(x)) == []
    assert list(Unit().match(x)) == []
    assert list(Tensor((A, A)).match(x @ y)) == []
    assert [s for s, _ in Tensor((A, A)).match(x @ x)] == [{"A": x}]
    assert next(Attr(A, "r").match(rigid.Ty("x").r))[0] == {"A": rigid.Ty("x")}
    subst, residuals = next(Op("<<", A, B).match(x))
    assert subst == {} and residuals == ((Op("<<", A, B), x), )
    subst, residuals = next(Call(M, "delay").match(x))
    assert residuals == ((Call(M, "delay"), x), )


def test_instantiate():
    subst = {"A": x @ y, "M": z}
    assert Tensor((A, M)).instantiate(subst, Ty) == x @ y @ z
    assert Unit().instantiate(subst, Ty) == Ty()
    assert Attr(M, "r").instantiate({"M": rigid.Ty("z")}, rigid.Ty)\
        == rigid.Ty("z").r
    assert Call(M, "delay").instantiate(
        {"M": monoidal.Ty("z")}, Ty) == monoidal.Ty("z").delay()\
        if hasattr(monoidal.Ty, "delay") else True
    assert Hom(A, M).instantiate(subst, Ty) == (x @ y, z)
    assert Tensor((A, M)).variables == ("A", "M")
    assert Op("<<", A, M).variables == ("A", "M")


def test_hom_match():
    hom = Hom(Tensor((A, B)), A)
    assert [s for s, _ in hom.match(x @ y, x)] == [{"A": x, "B": y}]
    assert [s for s, _ in hom.match(None, x)] == [{"A": x}]
    assert list(hom.match(x @ y, y)) == []


def test_sequent_str():
    assert str(Sequent()) == ""
    assert str(Sequent({"A": Sort()}, {"f": Hom(A, A)}, Hom(A, A)))\
        == "A: C0 | f: C1[A, A] ⊢ C1[A, A]"
    assert str(Sequent(premises={"x": Sort("C0", atomic=True)}))\
        == "x: Atom[C0]"


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
        def twice[A: C0](self: C1[A, A]) -> C1[A, A]:
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
    with raises(TypeError):
        @generator
        def wrong[A: C0](cls, f: C1[A, A]) -> C1[A, A]:
            ...
    assert type(declarations(rigid.Diagram, Generator)["cups"]) is Generator
    assert "cups" not in declarations(rigid.Diagram, Rule)
    assert rigid.Diagram.generators["cups"].category is rigid.Diagram
    assert str(braided.Diagram.generators["braid"]) == (
        "braid: X: Atom[C0], Y: Atom[C0] | left: X, right: Y"
        " ⊢ C1[X @ Y, Y @ X]")

    class Lying(Diagram):
        @classmethod
        @generator
        def wrong[A: C0](cls, dom: A) -> C1[A, 1]:
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


def test_axiom():
    assert MonoidalCategory.bifunctoriality.parameters[0].name == "f"
    assert str(MonoidalCategory.bifunctoriality.sequent).startswith(
        "A: C0, B: C0, C: C0, D: C0, E: C0, F: C0 | f: C1[A, B]")
    args = find(Diagram.bifunctoriality.strategy(), lambda _: True)
    f, g, h, k = args
    assert f.cod == h.dom and g.cod == k.dom
    assert Diagram.bifunctoriality(*args)
    assert MonoidalCategory.tensor.sequent.conclusion is not None
    assert Axiom.concludes is False
    with raises(TypeError):
        @axiom
        def eager(cls, f):
            """ An unannotated premise has no pattern. """


def test_weaken():
    law = MonoidalCategory.bifunctoriality.weaken(max_depth=0).bind(Diagram)
    args = find(law.strategy(), lambda _: True)
    assert all(len(term.boxes) <= 1 for term in args)
    assert law.weaken(max_depth=1).params == {"max_depth": 1}
    assert law.modulo(lambda term: term).params == law.params


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


def test_equation_of_axiom():
    assert isinstance(Diagram.unitality(Box("f", x, y)), Equation)
