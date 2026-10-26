from math import sqrt

from pytest import approx, raises

from discopy.optyx import Diagram, Encode, bit, mode, qubit
from discopy.optyx.classical import BitControlledGate
from discopy.optyx.contextuality import distributions
from discopy.optyx.photonic import NumberResolvingMeasurement
from discopy.optyx.qubits import H, Measure, Scalar, Z
from discopy.quantum.contextuality import Model, Scenario


alice = BitControlledGate(Z(1, 1, .25)) >> H() >> Measure(1)
bob = Diagram.swap(qubit, bit) >> bit @ Z(1, 1, -.125)\
    >> BitControlledGate(Z(1, 1, .25)) >> H() >> Measure(1)
bell_test = bit @ Scalar(.5 ** .5) @ Z(0, 2) @ bit >> alice @ bob
detector = Encode(mode) >> NumberResolvingMeasurement(1)


def test_from_diagram():
    tsirelson = Model.from_diagram(bell_test)
    p = (sqrt(2) + 2) / 8
    assert tsirelson.is_close(Model(Scenario.bell(2), 3 * [
        [p, 1 / 2 - p, 1 / 2 - p, p]] + [[1 / 2 - p, p, p, 1 / 2 - p]]))
    assert tsirelson.contextual_fraction() == approx(sqrt(2) - 1)
    assert Model.from_diagram(bell_test, outcomes=3).contextual_fraction(
        ) == approx(sqrt(2) - 1)
    counter = Model.from_diagram(detector @ detector, settings=(3, 1))
    assert counter.scenario == Scenario.bell(2, (3, 1), outcomes=3)
    assert counter.table[2] == (0, 0, 0, 0, 0, 0, 1, 0, 0)
    assert counter.contextual_fraction() == approx(0, abs=1e-9)


def test_from_diagram_unnormalised():
    unnormalised = bit @ Z(0, 2) @ bit >> alice @ bob
    assert all(sum(row.values()) == approx(2)
               for row in distributions(unnormalised, (2, 2)))
    model = Model.from_diagram(unnormalised)
    assert not model.is_compatible()
    with raises(ValueError):
        model.contextual_fraction()


def test_from_diagram_errors():
    with raises(ValueError):
        Model.from_diagram(Measure(1))
    with raises(ValueError):
        Model.from_diagram(detector @ Encode(mode))
    with raises(ValueError):
        distributions(detector, (2, 2))
    with raises(ValueError):
        Model.from_diagram(bell_test, settings=(3, 2))
    with raises(ValueError):
        Model.from_diagram(bell_test, settings=(0, 2))
    with raises(ValueError):
        Model.from_diagram(detector @ detector, settings=(3, 1), outcomes=2)
