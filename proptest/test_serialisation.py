"""
Property tests for tree serialisation: every carrier that implements
``to_tree`` decodes back to itself, both through raw trees and through JSON.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from discopy.utils import dumps, from_tree, loads, factory_name

from proptest.test_axioms import CARRIERS


def carrier_parameters():
    """ One parameter per carrier, skipping those without ``to_tree``. """
    for carrier in CARRIERS:
        marks = () if hasattr(carrier, "to_tree")\
            else pytest.mark.skip(reason="No tree serialisation.")
        yield pytest.param(carrier, marks=marks, id=factory_name(carrier))


@pytest.mark.parametrize("carrier", carrier_parameters())
@given(data=st.data())
@settings(max_examples=25, deadline=None)
def test_serialisation(carrier, data):
    """ Check that a value decodes back from its tree and its JSON. """
    value = data.draw(carrier.strategy())
    assert from_tree(value.to_tree()) == value
    assert loads(dumps(value)) == value
