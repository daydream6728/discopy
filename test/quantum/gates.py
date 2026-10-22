# -*- coding: utf-8 -*-
"""
Tests for :mod:`discopy.quantum.gates`.

Every box that narrows :code:`Box.__init__` needs a :code:`from_tree` of its
own, and where the tree does not hold what its constructor reads, a
:code:`to_tree` to put it there (discopy/discopy#780).
"""

import numpy
from pytest import importorskip, mark, raises

from discopy.quantum import bit, qubit
from discopy.quantum.gates import (
    CCX, CCZ, CRx, CRz, CU1, CX, CY, CZ, Bits, Bra, Controlled, Copy, Digits,
    Discard, Encode, H, Ket, Match, Measure, MixedScalar, MixedState, Rx, Ry,
    Rz, S, SWAP, Scalar, Sqrt, T, U1, X, Y, Z)
from discopy.utils import from_tree


def test_Encode_types():
    assert Encode().dom == bit and Encode().cod == qubit
    for destructive in (True, False):
        for override_bits in (True, False):
            measure = Measure(
                destructive=destructive, override_bits=override_bits)
            assert measure.dagger().dom == measure.cod
            assert measure.dagger().cod == measure.dom
    assert (Measure(destructive=False) >> Encode(constructive=False)).cod\
        == qubit


def test_Controlled_with_distance():
    assert Controlled(X, distance=-1).with_distance(1) == Controlled(X)
    assert CRz(0.25, distance=-1).with_distance(1) == CRz(0.25)
    for factory in (CRz, CRx, CU1):
        for distance in (-2, -1, 2, 3):
            assert factory(0.25, distance=distance).array is not None


def test_Sqrt():
    assert Sqrt(4).array == 2
    assert Sqrt(0).array == 0
    for data in (4, 2, -1, -2.5, 1j, 1 + 1j):
        assert numpy.isclose(
            (Sqrt(data) >> Sqrt(data).dagger()).eval().array, abs(data))
        assert Sqrt(data).dagger().dagger() == Sqrt(data)
    assert Sqrt(-1).dagger() != Sqrt(-1)
    assert numpy.isclose(Sqrt(-1).dagger().array, Sqrt(-1).array.conjugate())
    assert repr(Sqrt(-1).dagger()).endswith("[::-1]")
    root_two = Sqrt(2)
    assert root_two.dagger() is root_two
    with raises(ValueError):
        Sqrt(2, is_dagger=True)


def test_Sqrt_dagger_survives_substitution():
    phi = importorskip("sympy").Symbol("phi")
    assert Sqrt(phi).dagger().subs(phi, -1) == Sqrt(-1).dagger()
    assert Sqrt(phi).dagger().lambdify(phi)(-1) == Sqrt(-1).dagger()
    assert Sqrt(phi).dagger().subs(phi, 4) == Sqrt(4)


BOXES = [
    CCX, CCZ, CX, CY, CZ, H, S, SWAP, T, X, Y, Z,
    Rx(.25), Ry(.25), Rz(.25), U1(.25),
    CRx(.25), CRz(.25), CU1(.25), CRz(.25, distance=3),
    Controlled(X, distance=-2), Controlled(CX, distance=2),
    Scalar(.5), Scalar(.5, is_mixed=True), MixedScalar(.5), Sqrt(2),
    Sqrt(-1), Sqrt(-1).dagger(),
    Ket(1, 0), Bra(1, 0), Ket(0).dagger(), Copy(), Match(),
    Bits(1, 0), Bits(1, 0).dagger(), Digits(2, dim=4),
    Discard(), Discard(2), MixedState(), MixedState(2),
    Measure(), Measure(2, destructive=False), Measure(2, override_bits=True),
    Encode(), Encode(2, constructive=False), Encode(2, reset_bits=True),
]


@mark.parametrize("box", BOXES, ids=repr)
def test_to_from_tree(box):
    assert from_tree(box.to_tree()) == box


def test_to_from_tree_circuit():
    circuit = Ket(0, 0) >> CX >> Rz(.25) @ H >> Scalar(.5) @ Bra(0, 0)
    assert from_tree(circuit.to_tree()) == circuit


def test_Controlled_from_tree_reads_back_through_the_base():
    """
    A subclass such as :code:`CRz` takes the phase of the rotation it controls
    where :code:`Controlled` takes the gate itself, and the two are equal, so
    the tree of either reads back as a :code:`Controlled`.
    """
    assert CRz(.25) == Controlled(Rz(.25), distance=1)
    assert from_tree(CRz(.25).to_tree()) == CRz(.25)
    assert isinstance(from_tree(CRz(.25).to_tree()), Controlled)


def test_Measure_Encode_trees_carry_their_flags():
    assert Measure(2, destructive=False).to_tree()["destructive"] is False
    assert Measure(2, override_bits=True).to_tree()["override_bits"] is True
    assert Encode(2, constructive=False).to_tree()["constructive"] is False
    assert Encode(2, reset_bits=True).to_tree()["reset_bits"] is True


def test_Scalar_tree_carries_is_mixed():
    assert Scalar(.5, is_mixed=True).to_tree()["is_mixed"] is True
    assert from_tree(Scalar(.5, is_mixed=True).to_tree()).is_mixed is True
    assert from_tree(Scalar(.5).to_tree()).is_mixed is False


def test_Scalar_grad_keeps_is_mixed():
    phi = importorskip("sympy").Symbol("phi")
    derivative = Scalar(2 * phi, is_mixed=True).grad(phi)
    assert derivative.is_mixed
    assert numpy.isclose(derivative.eval(mixed=True).array, 2)


def test_Controlled_array_reads_the_dagger_of_its_gate():
    for gate in (S, T, Y, Rx(.3), Controlled(T, distance=-1)):
        controlled = Controlled(gate)
        dim = 2 ** len(controlled.dom)
        array = controlled.eval().array.reshape(dim, dim)
        assert numpy.allclose(
            controlled.dagger().eval().array.reshape(dim, dim),
            array.conj().T)
        assert numpy.allclose(
            (controlled >> controlled.dagger()).eval().array.reshape(
                dim, dim), numpy.eye(dim))


def test_Controlled_rotation_commutes_with_evaluation():
    for gate in (CRz(.3), CRx(.3), CU1(.3, distance=-2), Controlled(S),
                 Controlled(Y, distance=2), Controlled(CRz(.4), distance=-1)):
        assert gate.l.eval().is_close(gate.eval().l)
        assert gate.r.eval().is_close(gate.eval().r)
        assert gate.l.r == gate == gate.r.l
    assert isinstance(CRz(.5).rotate(), Controlled)


def test_subs_and_lambdify_keep_distance_and_is_mixed():
    phi = importorskip("sympy").Symbol("phi")
    for gate, expected in [
            (CRz(phi, distance=2), CRz(.5, distance=2)),
            (CRx(phi, distance=-1).delay(), CRx(.5, distance=-1).delay()),
            (Scalar(2 * phi, is_mixed=True), Scalar(1, is_mixed=True)),
            (MixedScalar(2 * phi), MixedScalar(1)), (Sqrt(phi), Sqrt(.5))]:
        for result in (gate.subs(phi, .5), gate.lambdify(phi)(.5)):
            assert result == expected and result.is_mixed == gate.is_mixed
            assert getattr(result, "distance", None)\
                == getattr(gate, "distance", None)
    gradient = Rz(phi).grad(phi).lambdify(phi)(.3).eval(mixed=True).array
    step = 1e-6
    assert numpy.allclose(gradient, (
        Rz(.3 + step).eval(mixed=True).array
        - Rz(.3 - step).eval(mixed=True).array) / (2 * step), atol=1e-4)


@mark.parametrize("mixed", [False, True])
@mark.parametrize("rotation", [Rx, Ry, Rz, U1])
def test_rotation_grad_is_the_finite_difference(rotation, mixed):
    phi = importorskip("sympy").Symbol("phi")
    gradient = rotation(2 * phi).grad(phi, mixed=mixed).lambdify(phi)(.3)
    step = 1e-6
    assert numpy.allclose(gradient.eval(mixed=mixed).array, (
        rotation(.6 + 2 * step).eval(mixed=mixed).array
        - rotation(.6 - 2 * step).eval(mixed=mixed).array) / (2 * step),
        atol=1e-4)
