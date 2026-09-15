""" Property tests for DisCoPy's principal categorical data structures. """

import pytest
from hypothesis import given, note
from hypothesis import strategies as st

from discopy.utils import factory_name

from proptest.categories import CATEGORIES
from proptest.conftest import PROFILE


def declaring(category: type, name: str) -> type:
    """
    The class whose declaration of the law of that name ``category``
    inherits: the first in its MRO with the name in its namespace.
    """
    return next(base for base in category.__mro__ if name in base.__dict__)


def once_per_declaration(cells: list) -> list:
    """
    One cell per declaration of a law, under the ``fast`` profile: the
    enrolled category nearest the class declaring it, so that a law is
    tested once bound to its defining class rather than again on every
    category inheriting it. A category restating an inherited law —
    broken, weakened or modulo a quotient — declares it anew.
    """
    nearest = {}
    for category, axiom in cells:
        owner = declaring(category, axiom.name)
        distance = category.__mro__.index(owner)
        if (owner, axiom.name) not in nearest\
                or distance < nearest[owner, axiom.name][0]:
            nearest[owner, axiom.name] = (distance, category, axiom)
    return [(category, axiom) for _, category, axiom in nearest.values()]


def axiom_parameters():
    """
    Translate every axiom of every category to a pytest parameter, one per
    declaration under the ``fast`` profile.

    An axiom taking no argument states its verdict without one, so we ask it
    here: :obj:`NotImplemented` means the structure does not apply and the
    test is skipped rather than generating arguments it could not satisfy.
    """
    cells = [
        (category, axiom)
        for category in CATEGORIES for axiom in category.axioms.values()]
    if PROFILE == "fast":
        cells = once_per_declaration(cells)
    for category, axiom in cells:
        if not axiom.parameters and axiom() is NotImplemented:
            marks = pytest.mark.skip(reason=axiom.__doc__.strip())
        elif axiom.broken:
            marks = pytest.mark.xfail(reason=axiom.__doc__.strip())
        else:
            marks = ()
        yield pytest.param(
            axiom, marks=marks, id=f"{factory_name(category)}.{axiom.name}")


@pytest.mark.parametrize("axiom", axiom_parameters())
@given(data=st.data())
def test_axiom(axiom, data):
    """ Check an axiom of a category against generated arguments. """
    equation = data.draw(axiom.strategy(), label=axiom.name)
    note(equation)
    assert equation
