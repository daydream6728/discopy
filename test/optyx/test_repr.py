"""
The transparency law of STYLE.md, i.e. :meth:`discopy.axioms.transparency`,
on every box of :mod:`discopy.optyx`.

A cell is only as strong as the equality it is checked by: the boxes whose
semantics live outside ``setoid`` — ``BBS``, ``TBS``, ``MZI``, ``Create``,
``DualRail`` and every ``CQMap`` — would pass a representation that dropped
a flag, see rel-int/discopy-next#386.
"""

import sys

import pytest

import discopy
from discopy import optyx
from discopy.optyx import channel, classical, photonic, qubits
from discopy.optyx.channel import bit, mode, qubit, qmode
from discopy.optyx.core import diagram


def environment(module):
    """The namespace a representation of ``module`` reads back in."""
    public = lambda namespace: {
        name: value for name, value in namespace.items()
        if not name.startswith("_")}
    return {**public(vars(discopy)), "optyx": optyx, **public(vars(module))}


CHANNEL = [
    channel.Channel("f", diagram.Id(diagram.mode)),
    channel.CQMap("g", diagram.Id(mode.double()), mode, mode),
    channel.Measure(qubit @ qmode),
    channel.Encode(bit @ mode),
    channel.Encode(mode, internal_states=([1, 0],)),
    channel.Discard(qubit),
    channel.Permutation(qubit @ bit @ mode, [2, 0, 1]),
    channel.Swap(qubit, bit),
    channel.Observable(operator=qubits.Z(1, 1, 0.25)),
]

QUBITS = [
    qubits.Z(1, 2), qubits.Z(1, 1, 0.25), qubits.X(2, 1), qubits.X(0, 1, 0.5),
    qubits.H(), qubits.Scalar(2), qubits.Scalar(0.5j),
    qubits.Ket(0), qubits.Ket("+"), qubits.Bra(1), qubits.Bra("-"),
    qubits.Measure(2), qubits.Encode(3), qubits.Discard(1),
    qubits.BitFlipError(0.1), qubits.DephasingError(0.2),
]

PHOTONIC = [
    photonic.Create(1, 0, 2), photonic.Select(1, 1),
    photonic.Scalar(2), photonic.Scalar(0.5),
    photonic.Encode(2), photonic.Discard(2),
    photonic.PhotonThresholdMeasurement(2),
    photonic.NumberResolvingMeasurement(2),
    photonic.Gate([[0, 1], [1, 0]], 2, 2, "flip"),
    photonic.Phase(0.25), photonic.NumOp(), photonic.HadamardBS(),
    photonic.BBS(0), photonic.BBS(0.5, is_conj=True),
    photonic.TBS(0.25), photonic.TBS(0.25, is_gate_dagger=True),
    photonic.MZI(0.25, 0.5), photonic.MZI(0.25, 0.5, is_conj=True),
    photonic.DualRail(2), photonic.PhaseShiftDR(0.25),
    photonic.Swap(1, 1), photonic.PhotonLoss(0.5),
]

CLASSICAL = [
    classical.Digit(1, 2), classical.PostselectDigit(1),
    classical.PostselectBit(0, 1),
    classical.Add(2), classical.CopyN(2), classical.CopyBit(3),
    classical.And(2), classical.Or(2), classical.Xor(2),
    classical.Not(), classical.Mod2(), classical.Divide(),
    classical.Multiply(), classical.Sub(), classical.H(),
    classical.SwapBit(), classical.SwapN(),
    classical.Scalar(2), classical.Z(1, 2), classical.X(2, 1, 0.5),
    classical.BinaryMatrix([[1, 0], [0, 1]]),
]


@pytest.mark.parametrize("box", CHANNEL + QUBITS + PHOTONIC + CLASSICAL,
                         ids=lambda box: type(box).__name__)
def test_transparency(box):
    module = sys.modules[type(box).__module__]
    assert eval(repr(box), environment(module)) == box


DIAGRAMS = [
    qubits.Z(1, 2) @ qubit >> qubit @ qubits.X(2, 1),
    photonic.Create(1, 1) >> photonic.BBS(0),
    classical.Digit(1) >> classical.Mod2(),
    channel.Discard(qmode) @ channel.Measure(bit),
]


@pytest.mark.parametrize("term", DIAGRAMS, ids=str)
def test_transparency_of_diagrams(term):
    assert eval(repr(term), environment(channel)) == term
