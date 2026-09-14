""" DisCoPy's property-testing module in action. """

from __future__ import annotations

from typing import Self

from hypothesis import find
from hypothesis import strategies as st
from hypothesis.errors import NoSuchExample
from pytest import raises

from discopy import cat, feedback, monoidal, rigid
from discopy.axioms import (
    Axiom, AxiomFailure, Equation, Relabelling, Strategy, assert_axioms,
    axiom)
from discopy.cat import Arrow, Box, Functor, Ob


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
    args = find(law.strategy(), lambda _: True)
    assert len(args[0].inside) <= 1 and law(*args)


def test_self_annotation():
    @axiom
    def absorbing(cls, f: Self) -> Equation:
        """ The identity on the domain absorbs into any arrow. """
        return Equation(cls.id(f.dom) >> f, f)

    law = absorbing.bind(Arrow)
    args = find(law.strategy(), lambda _: True)
    assert isinstance(args[0], Arrow) and law(*args)


def test_falsify():
    @axiom
    def trivial(cls, f: C1) -> Equation:
        """ Every arrow is an identity, which a box refutes. """
        return Equation(f, cls.id(f.dom))

    counterexample, = trivial.bind(Arrow).falsify()
    assert isinstance(counterexample, Arrow) and counterexample.inside
    assert Arrow.unitality.failing("Never holds.").falsify()
    with raises(NoSuchExample):
        Arrow.associativity.falsify()


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
    functor, obj = find(law.strategy(), lambda _: True)
    assert isinstance(functor, Functor) and isinstance(obj, Ob)
    assert law(functor, obj)


def test_monoid_law():
    law = monoidal.Ty.unitality.weaken(max_length=1)
    args = find(law.strategy(), lambda _: True)
    assert len(args[0]) <= 1 and law(*args)
