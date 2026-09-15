""" DisCoPy's property-testing module in action. """

from __future__ import annotations

from typing import Self

from hypothesis import find
from hypothesis.errors import NoSuchExample
from pytest import raises

from discopy import braided, cat, feedback, monoidal, rigid
from discopy.abc import MonoidalCategory
from discopy.axioms import (
    Axiom, AxiomFailure, Equation, Relabelling, assert_axioms, axiom)
from discopy.cat import Arrow, Box, Functor, Ob
from discopy.monoidal import Diagram
from discopy.pattern import C1
from discopy.utils import AxiomError


def test_axioms():
    assert_axioms(Arrow)

    class Classified(Arrow):
        """ A category with a broken law and an inapplicable one. """
        unitality = Arrow.unitality.failing("Never holds.")
        dagger_involution = Arrow.dagger_involution.inapplicable("No dagger.")

    assert_axioms(Classified)


def test_strategy():
    x, y = Ob('x'), Ob('y')
    find(Ob.strategy(), lambda ob: ob.name == "a")
    assert find(Arrow.strategy(dom=x, cod=x), lambda _: True) == Arrow.id(x)
    assert find(Arrow.strategy(dom=x, cod=y), lambda _: True).cod == y
    assert find(Arrow.strategy(dom=x), lambda _: True).dom == x
    assert find(Arrow.strategy(cod=y), lambda _: True).cod == y
    assert find(Box.strategy(dom=x), lambda _: True).dom == x


def test_axiom_binding():
    assert repr(Axiom(lambda cls: NotImplemented)) == "Axiom(<lambda>)"
    assert eval(repr(Arrow.unitality)) == cat.Arrow.unitality
    assert hash(Arrow.unitality) == hash(eval(repr(Arrow.unitality)))
    assert Arrow.unitality != Functor.unitality
    with raises(TypeError):
        Axiom(lambda cls: NotImplemented)()
    with raises(TypeError):
        Axiom(lambda cls: NotImplemented).falsify()
    with raises(TypeError):
        Axiom(lambda cls: NotImplemented).strategy()
    assert axiom(lambda cls: NotImplemented).bind(Arrow)() is NotImplemented
    box = Box('f', Ob('x'), Ob('y'))
    assert Arrow.unitality(box)
    broken = Arrow.unitality.weaken(max_leaves=1).failing("Never holds.")
    assert broken.params == {"max_leaves": 1}
    with raises(AxiomFailure) as failure:
        broken(box)
    assert failure.value.equation


def test_inapplicable():
    law = Arrow.unitality.inapplicable("No identities to cancel.")
    assert law.name == "unitality"
    assert law.__doc__ == "No identities to cancel."
    assert law() is NotImplemented


def test_modulo():
    law = Arrow.unitality.modulo(lambda term: term.dom).bind(Arrow)
    assert law(Box('f', Ob('x'), Ob('y')))


def test_weaken():
    law = Arrow.unitality.weaken(max_leaves=1).bind(Arrow)
    assert law.modulo(lambda term: term).params == law.params
    equation = find(law.strategy(), lambda _: True)
    assert equation and all(len(term.inside) <= 1 for term in equation.terms)


def test_self_annotation():
    @axiom
    def absorbing(cls, f: Self) -> Equation:
        """ The identity on the domain absorbs into any arrow. """
        return Equation(cls.id(f.dom) >> f, f)

    law = absorbing.bind(Arrow)
    equation = find(law.strategy(), lambda _: True)
    assert isinstance(equation.terms[1], Arrow) and equation


def test_falsify():
    @axiom
    def trivial(cls, f: C1) -> Equation:
        """ Every arrow is an identity, which a box refutes. """
        return Equation(f, cls.id(f.dom))

    equation = trivial.bind(Arrow).falsify()
    assert not equation and equation.terms[0].inside
    for law in (Arrow.associativity, Arrow.unitality.failing("Declared.")):
        with raises(NoSuchExample):
            law.falsify()


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


def test_Relabelling():
    x, y, z = cat.Ob('x'), cat.Ob('y'), cat.Ob('z')
    relabelling = Relabelling(((x, y), ))
    assert relabelling[x] == y and relabelling[z] == z
    assert list(relabelling) == [x] and len(relabelling) == 1
    assert bool(Relabelling())
    assert relabelling[cat.Box('f', x, x)] == cat.Box('f', y, y)
    rigid_x, rigid_y = rigid.Ty('x'), rigid.Ty('y')
    rotating = Relabelling(((rigid_x, rigid_y), ))
    functor = rigid.Functor(rotating, rotating)
    assert functor(rigid_x.l) == rigid_y.l and functor(rigid_x.r) == rigid_y.r
    rotated = rigid.Box('f', rigid_x.r, rigid_x @ rigid_x)
    assert rotating[rotated] == rigid.Box('f', rigid_y.r, rigid_y @ rigid_y)
    delayed = Relabelling(((feedback.Ty('u'), feedback.Ty('v')), ))
    delaying = feedback.Box('f', feedback.Ty('u').delay(), feedback.Ty('u'))
    assert delayed[delaying] == feedback.Box(
        'f', feedback.Ty('v').delay(), feedback.Ty('v'))


def test_functor_law():
    @axiom
    def preserves_identity(cls, functor: Self, x: Self.dom.ob) -> Equation:
        """ A functor preserves the identity on each object. """
        return Equation(
            functor(cls.dom.id(x)), functor.cod.id(functor(x)))

    law = preserves_identity.bind(Functor)
    equation = find(law.strategy(), lambda _: True)
    assert equation and all(isinstance(t, Arrow) for t in equation.terms)


def test_monoid_law():
    law = monoidal.Ty.unitality.weaken(max_length=1)
    equation = find(law.strategy(), lambda _: True)
    assert equation and all(len(term) <= 1 for term in equation.terms)


def test_axiom():
    assert MonoidalCategory.bifunctoriality.parameters[0].name == "f"
    assert str(MonoidalCategory.bifunctoriality.sequent).startswith(
        "A: C0, B: C0, C: C0, D: C0, E: C0, F: C0 | f: C1[A, B]")
    equation = find(Diagram.bifunctoriality.strategy(), lambda _: True)
    assert equation and len(equation.terms) == 2
    assert MonoidalCategory.tensor.sequent.conclusion is not None
    assert Axiom.concludes is False
    with raises(TypeError):
        @axiom
        def eager(cls, f):
            """ An unannotated premise has no pattern. """


def test_weaken_params():
    law = MonoidalCategory.bifunctoriality.weaken(max_depth=0).bind(Diagram)
    equation = find(law.strategy(), lambda _: True)
    assert equation and all(len(term.boxes) <= 4 for term in equation.terms)
    assert law.weaken(max_depth=1).params == {"max_depth": 1}
    assert law.modulo(lambda term: term).params == law.params


def test_equation_of_axiom():
    x, y = monoidal.Ty('x'), monoidal.Ty('y')
    assert isinstance(Diagram.unitality(monoidal.Box("f", x, y)), Equation)


def test_canonical():
    equation = Diagram.bifunctoriality.canonical()
    assert equation and str(equation.terms[0])\
        == "f @ C >> B @ g >> h @ D >> E @ k"
    assert str(Arrow.associativity.canonical())\
        == "Equation(f >> g >> h, f >> g >> h)"
    assert str(Diagram.tensor_unitality.canonical())\
        == "Equation(Id(x @ y), Id(x @ y))"
    assert Arrow.unitality.failing("Declared.").canonical()
    assert not braided.Diagram.braid_naturality.canonical()
    inapplicable = Arrow.unitality.inapplicable("No identities.")
    assert inapplicable.canonical() is NotImplemented
    with raises(TypeError, match="nothing to draw"):
        inapplicable.draw()
    assert str(rigid.Diagram.snake_equations.canonical().terms[1]) == "Id(x)"
    cups = rigid.Diagram.generators["cups"].canonical()
    assert cups == (rigid.Ty('X'), rigid.Ty('X').r)
    with raises(AxiomError):
        feedback.Diagram.feedback_joining.canonical()
