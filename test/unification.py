# -*- coding: utf-8 -*-

from random import Random

import pytest

from discopy import closed, feedback, rigid
from discopy.neural.network import Dims, Network
from discopy.unification import Unifier
from discopy.utils import AxiomError


def test_delays():
    """ Unification undoes the delays of a conclusion. """
    x, y = feedback.Ty('x'), feedback.Ty('y')
    unifier = Unifier(feedback.Diagram, Random(0), (x, ), None)
    first, second = unifier.fresh(x), unifier.fresh(x)
    unifier.unify(first @ second.delay(), x @ y.delay())
    assert (unifier.resolve(first), unifier.resolve(second)) == (x, y)
    with pytest.raises(AxiomError):
        unifier.unify(first, y)


def test_adjoints():
    """ Unification undoes the adjoints of a cup. """
    x = rigid.Ty('x')
    unifier = Unifier(rigid.Diagram, Random(0), (x, ), None)
    left, right = unifier.fresh(x), unifier.fresh(x)
    unifier.unify(left @ left.r, right @ x.r)
    assert unifier.resolve(left) == unifier.resolve(right) == x


def test_exponentials():
    """ Unification goes into the base and exponent of an exponential. """
    x, y = closed.Ty('x'), closed.Ty('y')
    unifier = Unifier(closed.Diagram, Random(0), (x, ), None)
    base, exponent = unifier.fresh(x), unifier.fresh(x)
    unifier.unify(base << exponent, x << y)
    assert (unifier.resolve(base), unifier.resolve(exponent)) == (x, y)


def test_numbered():
    """ The placeholders of an object with no name are numbered. """
    unifier = Unifier(Network, Random(0), (Dims(2), ), None)
    first, second = unifier.fresh(Dims(2)), unifier.fresh(Dims(2) @ Dims(2))
    unifier.unify(first @ first, Dims(3) @ Dims(3))
    unifier.unify(second, Dims(2) @ Dims(3))
    assert unifier.resolve(first) == Dims(3)
    assert unifier.resolve(second) == Dims(2) @ Dims(3)


def test_colour():
    """ A placeholder no rule determines is coloured from the palette. """
    x = rigid.Ty('x')
    unifier = Unifier(rigid.Diagram, Random(0), (x, ), None)
    assert unifier.resolve(unifier.fresh(x)) == x
