"""
Properties of quantum reservoir computing, which are functions rather than
the laws of a category.
"""

from hypothesis import given
from hypothesis import strategies as st
from numpy import allclose

from discopy.quantum import Ket, Measure
from discopy.quantum.reservoir import Reservoir

reservoirs = st.builds(
    Reservoir.random, memory=st.integers(1, 2), inputs=st.integers(1, 2),
    depth=st.integers(1, 2), seed=st.integers(0, 2 ** 16))
values = st.floats(0, 2, allow_nan=False)


def sequences(reservoir):
    """ Sequences of a reservoir's input values, one per step. """
    return st.lists(
        st.tuples(*reservoir.inputs * [values]), min_size=1, max_size=3)


@given(reservoirs.flatmap(lambda r: st.tuples(st.just(r), sequences(r))))
def test_features_are_distributions(args):
    """ The features of each step are a probability distribution. """
    reservoir, sequence = args
    for features in reservoir.run(sequence):
        assert allclose(features.sum(), 1) and (features > -1e-9).all()


@given(reservoirs.flatmap(lambda r: st.tuples(st.just(r), sequences(r))))
def test_run_is_fold_of_step(args):
    """ Running a sequence measures the composite of its steps. """
    reservoir, sequence = args
    state = Ket(*reservoir.memory * [0])
    for step in sequence:
        state = state >> reservoir.step(*step)
    born = (state >> Measure(reservoir.memory)).eval().array
    assert allclose(reservoir.run(sequence)[-1], born.real.reshape(-1))


@given(st.integers(1, 2), st.integers(0, 2 ** 16))
def test_random_determinism(memory, seed):
    """ A random reservoir depends on its seed only. """
    assert Reservoir.random(memory, seed=seed)\
        == Reservoir.random(memory, seed=seed)
