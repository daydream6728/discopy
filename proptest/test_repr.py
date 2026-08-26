"""
Property tests for transparency: ``eval(repr(x)) == x`` in a fresh
environment, for every carrier of the property matrix.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from discopy import monoidal
from discopy.utils import factory_name

from proptest.test_axioms import CARRIERS

IMPORTS = (
    "from discopy import *",
    "import numpy as np",
    "from discopy.matrix import Matrix",
    "from discopy.python.finset import Function, Permutation",
    "from discopy.testing import Relabelling, Relabelled",
)
"""
What the fresh environment loads: the package itself, plus the obvious
import for each carrier whose ``repr`` uses its bare class name — ``Matrix``
and ``finset`` print unqualified, and a generated functor relabels the
generators through :class:`discopy.testing.Relabelling`.
"""

ENVIRONMENT = {}
for statement in IMPORTS:
    exec(statement, ENVIRONMENT)


def carrier_parameters():
    """ One parameter per carrier, the uncoloured wire an expected failure. """
    for carrier in CARRIERS:
        marks = pytest.mark.xfail(reason=(
            "An uncoloured wire reprs as the cat.Ob that Ty coerces, "
            "which Wire.__eq__ rejects.")) if carrier is monoidal.Wire else ()
        yield pytest.param(carrier, marks=marks, id=factory_name(carrier))


@pytest.mark.parametrize("carrier", carrier_parameters())
@given(data=st.data())
@settings(max_examples=25, deadline=None)
def test_repr(carrier, data):
    """ Check that ``repr`` evaluates back to the value it describes. """
    value = data.draw(carrier.strategy())
    assert eval(repr(value), dict(ENVIRONMENT)) == value
