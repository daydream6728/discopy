""" Property tests for DisCoPy's principal categorical data structures. """

import pytest
from hypothesis import given, note
from hypothesis import strategies as st

from discopy.axioms import inhabits, position
from discopy.utils import factory_name

from proptest.categories import CATEGORIES, category_parameters


def axiom_parameters():
    """
    Translate every axiom of every category to a pytest parameter.

    An axiom declared :meth:`~discopy.axioms.Declaration.inapplicable` is
    skipped rather than generating arguments it could not satisfy. A
    category need not state laws at all: one enrolled for the ad-hoc
    properties only, such as a type of wires, has no ``axioms``.
    """
    for category in CATEGORIES:
        for axiom in category.axioms.values():
            if not axiom.applicable:
                marks = pytest.mark.skip(reason=axiom.__doc__.strip())
            elif axiom.broken:
                marks = pytest.mark.xfail(reason=axiom.__doc__.strip())
            else:
                marks = ()
            yield pytest.param(
                axiom, marks=marks,
                id=f"{factory_name(category)}.{axiom.name}")


@pytest.mark.cell
@pytest.mark.parametrize("axiom", axiom_parameters())
@given(data=st.data())
def test_axiom(axiom, drawn, data):
    """
    Check an axiom of a category against generated arguments, and the
    equation it states against the type of its output, evaluated in the
    scope its arguments were drawn in, recording the distinct terms it was
    checked on: a cell whose strategy draws the same handful however long
    the search runs is green about those terms rather than about the law,
    see :mod:`proptest.report`.
    """
    scope, arguments = data.draw(
        axiom.sequents(**axiom.params), label=axiom.name)
    drawn.add(repr(arguments))
    verdict = axiom(**arguments)
    note(verdict)
    assert inhabits(verdict, axiom.output(scope))
    assert verdict


@pytest.mark.parametrize("category", category_parameters())
def test_position(category):
    """
    Every ``C0`` and ``C1`` above an enrolled category stands for its
    objects and its arrows, as :meth:`discopy.abc.Category.parameters` says,
    whichever class states it and however its bases pass it on, so that a
    sequent bound to the category reads as one of its own.
    """
    for klass in category.__mro__:
        for parameter in getattr(klass, "__type_params__", ()):
            if parameter.__name__ in ("C0", "C1"):
                assert position(parameter, category)\
                    == int(parameter.__name__[1]), (klass, parameter)
