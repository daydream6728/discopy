"""
Property tests for the rewriting methods: ``normal_form`` and ``foliation``
are idempotent and preserve the diagram up to hypergraph.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from discopy import monoidal, rigid
from discopy.quantum import zx
from discopy.utils import factory_name

from proptest.test_axioms import CARRIERS

PARTIAL_HYPERGRAPH = pytest.mark.xfail(reason=(
    "to_hypergraph rejects a left-handed cup or cap: Hypergraph.cups and "
    "caps only accept the right-adjoint orientation."))

WRONG_SPIDER_FACTORY = pytest.mark.xfail(reason=(
    "The functor image of a spider is built by tensor's spider factory, "
    "which expects dimensions rather than PRO types."))


def diagram_parameters(xfail=()):
    """ One parameter per diagram carrier, with per-test expected failures. """
    for carrier in CARRIERS:
        if not (isinstance(carrier, type)
                and issubclass(carrier, monoidal.Diagram)):
            continue
        if carrier is rigid.Diagram:
            marks = PARTIAL_HYPERGRAPH
        elif carrier in xfail:
            marks = WRONG_SPIDER_FACTORY
        else:
            marks = ()
        yield pytest.param(carrier, marks=marks, id=factory_name(carrier))


DIAGRAMS = tuple(diagram_parameters())


@pytest.mark.parametrize("carrier", DIAGRAMS)
@given(data=st.data())
@settings(max_examples=25, deadline=None)
def test_normal_form(carrier, data):
    """ Check that ``normal_form`` is an idempotent representative. """
    diagram = data.draw(carrier.strategy())
    normal = diagram.normal_form()
    assert (normal.dom, normal.cod) == (diagram.dom, diagram.cod)
    assert normal.normal_form() == normal
    assert normal.to_hypergraph() == diagram.to_hypergraph()


@pytest.mark.parametrize(
    "carrier", tuple(diagram_parameters(xfail=(zx.Diagram, ))))
@given(data=st.data())
@settings(max_examples=25, deadline=None)
def test_foliation(carrier, data):
    """ Check that ``foliation`` is an idempotent representative. """
    diagram = data.draw(carrier.strategy())
    foliated = diagram.foliation()
    assert (foliated.dom, foliated.cod) == (diagram.dom, diagram.cod)
    assert foliated.foliation() == foliated
    assert foliated.to_hypergraph() == diagram.to_hypergraph()
