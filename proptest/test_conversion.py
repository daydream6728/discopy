"""
Property tests for the conversions between diagrams, hypergraphs and maps.

Each representation has a canonical decoder ``to_diagram``: the roundtrip
through a diagram must land back on the representation it started from, i.e.
``to_diagram`` is a section of ``to_hypergraph`` and of ``to_map``, and every
conversion preserves ``dom`` and ``cod``.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from discopy import (
    balanced,
    biclosed,
    closed,
    compact,
    feedback,
    frobenius,
    markov,
    monoidal,
    pivotal,
    symmetric,
    traced,
)

NO_SWAPS = pytest.mark.xfail(reason=(
    "Decoding a trace, cup or cap can cross wires, "
    "which needs swaps the category does not have."))


def levels(*modules, xfail=()):
    """ Translate the levels of the hierarchy to pytest parameters. """
    return tuple(
        pytest.param(
            module, id=module.__name__.removeprefix("discopy."),
            marks=NO_SWAPS if module in xfail else ())
        for module in modules)


HYPERGRAPH_LEVELS = levels(
    monoidal, traced, balanced, symmetric, pivotal, compact, markov,
    closed, feedback, frobenius, xfail=(traced, balanced, pivotal))

CMAP_LEVELS = levels(
    monoidal, traced, balanced, symmetric, biclosed, pivotal, compact,
    markov, closed, frobenius, xfail=(traced, balanced, pivotal))

COMMON_LEVELS = levels(monoidal, traced, balanced, symmetric, pivotal, compact)
"""
The levels whose two encodings agree: ``markov``, ``closed`` and ``frobenius``
are left out because ``to_hypergraph`` encodes their copies and spiders as
spiders while ``to_map`` keeps them as boxes.
"""


@pytest.mark.parametrize("module", HYPERGRAPH_LEVELS)
@given(data=st.data())
@settings(max_examples=25, deadline=None)
def test_hypergraph_section(module, data):
    """ ``to_diagram`` is a section of ``to_hypergraph``. """
    diagram = data.draw(module.Diagram.strategy())
    graph = diagram.to_hypergraph()
    assert (graph.dom, graph.cod) == (diagram.dom, diagram.cod)
    decoded = graph.to_diagram()
    assert (decoded.dom, decoded.cod) == (diagram.dom, diagram.cod)
    assert decoded.to_hypergraph() == graph


@pytest.mark.parametrize("module", CMAP_LEVELS)
@given(data=st.data())
@settings(max_examples=25, deadline=None)
def test_cmap_section(module, data):
    """ ``to_diagram`` is a section of ``to_map``. """
    diagram = data.draw(module.Diagram.strategy())
    map_ = diagram.to_map()
    assert (map_.dom, map_.cod) == (diagram.dom, diagram.cod)
    decoded = map_.to_diagram()
    assert (decoded.dom, decoded.cod) == (diagram.dom, diagram.cod)
    assert decoded.to_map() == map_


@pytest.mark.parametrize("module", COMMON_LEVELS)
@given(data=st.data())
@settings(max_examples=25, deadline=None)
def test_cmap_hypergraph_agreement(module, data):
    """ Encoding through a map or directly gives the same hypergraph. """
    diagram = data.draw(module.Diagram.strategy())
    assert diagram.to_map().to_hypergraph() == diagram.to_hypergraph()
