"""
Overview
--------

The distributions of the outcomes of a diagram for each choice of settings,
the empirical model :meth:`discopy.quantum.contextuality.Model.from_diagram`
computes the contextual fraction of.

Functions
---------

.. autosummary::
    :template: function.rst
    :nosignatures:
    :toctree:

    distributions

Example
-------
A Bell test at the Tsirelson bound, with a classical input for the setting
and a classical output for the outcome of each party, the setting
controlling a phase on its qubit before it is measured:

>>> from discopy.optyx import bit, qubit, Diagram
>>> from discopy.optyx.qubits import Z, H, Scalar, Measure
>>> from discopy.optyx.classical import BitControlledGate
>>> from discopy.quantum.contextuality import Model
>>> alice = BitControlledGate(Z(1, 1, .25)) >> H() >> Measure(1)
>>> bob = Diagram.swap(qubit, bit) >> bit @ Z(1, 1, -.125)\\
...     >> BitControlledGate(Z(1, 1, .25)) >> H() >> Measure(1)
>>> bell_test = bit @ Scalar(.5 ** .5) @ Z(0, 2) @ bit >> alice @ bob
>>> tsirelson = Model.from_diagram(bell_test)
>>> round(tsirelson.contextual_fraction(), 6)  # sqrt(2) - 1
0.414214
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import product

from discopy.optyx.channel import Diagram
from discopy.optyx.classical import Bit, Digit


def distributions(diagram: Diagram, settings: Sequence[int], backend=None
                  ) -> list[dict[tuple[int, ...], float]]:
    """
    The probability of each tuple of outcomes of a diagram with one classical
    input and one classical output for each party, for each choice of one
    input value below the number of settings of each party, in
    lexicographic order. The probabilities are not normalised, so that a
    postselected diagram is not conditioned on its success, and those that
    are zero are left out.

    Parameters:
        diagram : A diagram with classical domain and codomain of the same
            length.
        settings : The number of settings of each party, at most two for
            a ``bit`` input.
        backend : The backend evaluating the diagram.

    Example
    -------
    >>> from discopy.optyx import Encode, mode
    >>> from discopy.optyx.photonic import NumberResolvingMeasurement
    >>> counter = Encode(mode) >> NumberResolvingMeasurement(1)
    >>> distributions(counter, settings=(3, ))
    [{(0,): 1.0}, {(1,): 1.0}, {(2,): 1.0}]
    """
    dom, cod = diagram.dom.inside, diagram.cod.inside
    if len(dom) != len(cod) or len(dom) != len(settings) or not all(
            ob.is_classical for ob in dom + cod):
        raise ValueError(
            "The domain and codomain must be classical types of the same "
            f"length as {settings}, got {diagram.dom} and {diagram.cod}.")
    if any(n < 1 or ob.name == "bit" and n > 2
           for ob, n in zip(dom, settings)):
        raise ValueError(f"Each party has at least one setting, at most two "
                         f"for a bit input: {settings}.")
    return [{
        tuple(map(int, section)): float(probability)
        for section, probability in (Diagram.tensor(*(
            Bit(x) if ob.name == "bit" else Digit(x)
            for x, ob in zip(choice, dom))) >> diagram
        ).eval(backend).prob_dist(normalise=False).items() if probability > 0}
        for choice in product(*map(range, settings))]
