""" DisCoPy's property-testing module in action. """

from typing import Self, TypeVar

from hypothesis import Phase, find, settings
from hypothesis import strategies as st
from hypothesis.errors import NoSuchExample
from pytest import raises

from discopy import braided, cat, monoidal, rigid
from discopy.abc import Category, ColouredMonoid, Group, MonoidalCategory, Nat
from discopy.axioms import (
    L, R, Atom, Axiom, AxiomFailure, Equation, Equivalence, Hom, Obj, Over,
    Related, Repeat, Tensor, Testable, Under, Unit, Var,
    axiom, inhabits, position, substitute)
from discopy.cat import Arrow, Box, Functor, Ob
from discopy.monoidal import Ty


class ParityEquation(Equation):
    """ An equation between integers which holds up to their parity. """

    up_to = staticmethod(lambda n: n % 2)


class Parity(int, Equivalence):
    """ An integer up to parity, an equivalence relation besides equality. """

    equivalence_factory = ParityEquation

    @classmethod
    def strategy(cls, **params):
        """ Generate an integer, no strategy being enrolled from a test. """
        return st.integers().map(cls)

    @classmethod
    def related(cls, **params):
        """ Generate an integer, another of the same parity and any third. """
        return st.tuples(st.integers(), st.integers(), st.integers()).map(
            lambda triple: (
                cls(triple[0]), cls(triple[0] + 2 * triple[1]),
                cls(triple[2])))


def test_Equivalence():
    assert Parity.equivalent(Parity(1), Parity(3), Parity(-5))
    assert not Parity.equivalent(Parity(1), Parity(2))
    assert Parity.reflexivity(Parity(2))
    assert Parity.symmetry(Related[Parity]((1, 3, 4)))
    assert Parity.transitivity(Related[Parity]((1, 3, 5)))
    assert Parity.transitivity(Related[Parity]((1, 3, 4)))
    assert not Parity.transitivity(Related[Parity]((1, 2, 3)))
    assert find(Related[Parity].strategy(), lambda t: t[2] % 2 == 1)[2] % 2
    with raises(ValueError):
        Related[Parity]((1, 3))
    arguments = find(
        Parity.transitivity.arguments(), lambda arguments: True)
    assert isinstance(arguments["terms"], Related[Parity])


def test_failing_when_the_terms_do_not_build():
    class Refusing(Arrow):
        @axiom
        def refusing(cls, f: Self) -> Equation:
            raise ValueError("No terms.")
        refusing = refusing.failing("Declared broken.")

    with raises(AxiomFailure) as error:
        Refusing.refusing(f=Arrow.id(Ob('x')))
    assert isinstance(error.value.equation, ValueError)


def test_strategy():
    x, y = Ob('x'), Ob('y')
    find(Ob.strategy(), lambda ob: ob.name == "a")
    arrow = find(Arrow.search(dom=x, cod=y), lambda f: len(f) > 1)
    assert (arrow.dom, arrow.cod) == (x, y)
    identity = find(
        Arrow.search(fuel=0, within=Category), lambda f: not f.inside)
    assert identity == Arrow.id(identity.dom)
    assert find(Box.strategy(dom=x), lambda _: True).dom == x


def test_equation():
    f = Box('f', Ob('x'), Ob('x'))
    assert Equation(f, f, f).symbols == ("=", "=")
    with raises(ValueError):
        Equation(f, f, symbols=("=", "="))


def test_substitute_unhashable():
    """ A value that does not hash is never looked up in the scope. """
    A = TypeVar("A")
    unhashable = [Ty('x')]
    assert substitute(Var[list, A], {A: unhashable}).__args__ == (
        list, unhashable)


def test_position_of_a_group():
    """ The ``C1`` of a group is its arrows, as for any category. """
    assert position(Group.__type_params__[0], Group) == 1


def test_axiom_binding():
    assert repr(Axiom(lambda cls: NotImplemented)) == "Axiom(<lambda>)"
    assert eval(repr(Arrow.unitality)) == cat.Arrow.unitality
    assert hash(Arrow.unitality) == hash(eval(repr(Arrow.unitality)))
    assert Arrow.unitality != Functor.unitality
    with raises(TypeError):
        Axiom(lambda cls: NotImplemented)()
    with raises(TypeError):
        Axiom(lambda cls: NotImplemented).falsify()
    assert axiom(lambda cls: NotImplemented).bind(Arrow)() is NotImplemented
    box = Box('f', Ob('x'), Ob('y'))
    assert Arrow.unitality(f=box)
    broken = Arrow.unitality.weaken(max_leaves=1).failing("Never holds.")
    assert broken.params == {"max_leaves": 1}
    with raises(AxiomFailure) as failure:
        broken(f=box)
    assert failure.value.equation


def test_string_annotations():
    """ A law whose annotations are strings reads them as objects. """
    namespace = {}
    exec("from __future__ import annotations\n"
         "from discopy.axioms import Equation, Hom, Obj\n"
         "def deferred[A: Obj[int]](cls, f: Hom[int, A, A])"
         " -> Equation[Hom[int, A, A]]: return NotImplemented", namespace)
    law = axiom(namespace["deferred"]).bind(Arrow)
    (A, ), annotations = law.function.__type_params__, law.annotations()
    assert annotations["f"] == Hom[int, A, A]
    assert annotations["return"] == Equation[Hom[int, A, A]]


def test_sequents():
    @axiom
    def law[X: Atom[Ty], Y: Obj[Ty], N: Nat](
            cls, x: Var[Ty, X], f: Hom[Self, X, Y], term: Self,
            n: Var[Nat, N]
    ) -> Equation[tuple[int, Var[Ty, X], bool, bool]]:
        """ Quantify over an atom, a morphism out of it, a term and a
        number. """
        return Equation(
            (len(x), f.dom, isinstance(term, cls),
             isinstance(n, Nat) and n.n <= 3),
            (1, x, True, True))

    bound = law.bind(monoidal.Diagram)
    scope, arguments = find(bound.sequents(), lambda _: True)
    assert set(arguments) == {"x", "f", "term", "n"} and bound(**arguments)
    assert inhabits(bound(**arguments), bound.output(scope))


def test_formers():
    x, y = rigid.Ty('x'), rigid.Ty('y')
    assert Tensor[x, y] == x @ y and Unit[rigid.Ty] == rigid.Ty()
    assert (L[x], R[x]) == (x.l, x.r) and Repeat[x, 3] == x @ x @ x
    assert (Over[x, y], Under[y, x]) == (x << y, y >> x)
    f = rigid.Box('f', x, y)
    assert inhabits(f, Hom[rigid.Diagram, x, y])
    assert not inhabits(f, Hom[rigid.Diagram, y, x])
    assert not inhabits(Equation(f), Equation[Hom[rigid.Diagram, x, x]])


def test_classifiers():
    f = Box('f', Ob('x'), Ob('y'))
    broken = Arrow.unitality.failing("Never holds.")
    with raises(AxiomFailure) as failure:
        broken(f=f)
    assert broken.broken and failure.value.equation
    law = Arrow.unitality.inapplicable("No identities to cancel.")
    assert law() is NotImplemented
    assert law.__doc__ == "No identities to cancel."
    assert not law.applicable and Arrow.unitality.applicable
    assert Arrow.unitality.modulo(lambda term: term.dom)(f=f)


def test_rules():
    x, y = Ob('x'), Ob('y')
    f = Box('f', x, y)
    assert sorted(Arrow.rules) == ["ax", "cut"]
    assert Arrow.cut(f, f[::-1]) == f >> f[::-1] and Arrow.ax(x) == Arrow.id(x)
    assert Arrow.cut.is_recursive and not Arrow.ax.is_recursive
    assert monoidal.Diagram.mix.conclusion == (None, None)
    assert Arrow.ax.given(x, y) == {"X": y}


def test_equation_symbols():
    x = Ob('x')
    f, g = Box('f', x, x), Box('g', x, x)
    assert Equation(f).symbols == ()
    assert Equation(f, g, symbol="<").symbols == ("<", )
    assert Equation(f, f, g).symbols == ("=", "=")
    with raises(ValueError):
        Equation(f, g, symbols=("=", "="))


def test_weaken():
    law = Arrow.unitality.weaken(within=Category)
    assert law.params == {"within": Category}
    assert law(**find(law.strategy(), lambda _: True))
    args = find(law.strategy(), lambda _: True, settings=settings(
        max_examples=1, database=None, phases=(Phase.generate, )))


def test_weaken_shape_of_self():
    from discopy.biclosed import TermBase, Ty as Type
    x = Type("x")
    for law in (TermBase.symmetry, TermBase.alpha_renaming,
                TermBase.alpha_completeness):
        with raises(NoSuchExample):
            find(law.weaken(cod=x).strategy(),
                 lambda arguments: any(
                     term.cod != x for term in arguments["terms"]),
                 settings=settings(max_examples=50, database=None))


def test_falsify():
    @axiom
    def trivial[A: Obj[Ob], B: Obj[Ob]](
            cls, f: Hom[Self, A, B]) -> Equation[Self]:
        """ Every arrow is an identity, which a box refutes. """
        return Equation(f, cls.id(f.dom))

    assert trivial.bind(Arrow).falsify()["f"].inside
    assert Arrow.unitality.failing("Never holds.").falsify()
    with raises(NoSuchExample):
        Arrow.associativity.falsify(
            settings=settings(max_examples=50, database=None))




def test_axioms_of_category():
    class Broken(Arrow):
        """ A category declaring an inherited law broken. """
        unitality = Arrow.unitality.failing("Never holds.")

    assert Broken.axioms["unitality"].broken
    assert not Arrow.axioms["unitality"].broken

    class Hidden(Arrow):
        """ Assigning a non-axiom over an inherited law drops it. """
        unitality = None

    assert "unitality" not in Hidden.axioms


def test_matrix():
    assert monoidal.Diagram in Testable.enrolled()
    assert monoidal.Ty in Testable.enrolled()
    assert cat.FreeCategory not in Testable.enrolled()
    once = Testable.matrix(once=True)
    assert cat.Arrow.dagger_involution in once
    assert rigid.Diagram.unitality not in once
    assert set(once) <= set(Testable.matrix())




def test_copying():
    x, y = Ob('x'), Ob('y')
    assert Arrow.copying(term=Box('f', x, y))
    assert "copying" in Arrow.axioms and "copying" in Ob.axioms


def test_str_transparency():
    from hypothesis.errors import Unsatisfiable
    from discopy import biclosed, closed, monoidal
    x, y = monoidal.Ty('x'), monoidal.Ty('y')
    f = monoidal.Box('f', x, y)
    diagram = f @ x >> f[::-1] @ x
    assert monoidal.Diagram.str_environment(diagram)['f'] == f
    assert monoidal.Diagram.str_transparency(term=diagram)
    X, Y = biclosed.Ty('X'), biclosed.Ty('Y')
    assert biclosed.TermBase.str_transparency(
        term=X(lambda v: (Y << X)('g')(v)))
    E = closed.Ty('E')
    query = (E >> E)('query')
    assert closed.TermBase.str_transparency(term=query(query(E('e'))))
    F = closed.Ty('F')
    assert closed.Ty.str_transparency(term=(E * F) >> E.product(F, E))
    U = closed.Ty(closed.Unitype())
    assert closed.Ty.str_transparency(term=E.product(U) >> U.delay())
    assert find(Box.strategy(), lambda _: True).name.isidentifier()
    for clash in [monoidal.Box('x', x, x), monoidal.Box('Id', x, x)]:
        with raises(NameError):
            monoidal.Diagram.str_environment(clash)
        with raises(Unsatisfiable):
            find(st.just(clash), lambda term: monoidal.Diagram
                 .str_transparency(term=term))


def test_environment_binds_numpy_scalar_types():
    """ A dtype numpy names reads back, after the package names, see #162. """
    import numpy as np
    from discopy import matrix, tensor
    box = tensor.Box[np.float32]('f', tensor.Dim(2), tensor.Dim(2), [1., 0, 0, 1])
    environment = type(box).environment()
    assert eval(repr(box), environment) == box
    assert environment['matrix'] is matrix and 'bool' not in environment
