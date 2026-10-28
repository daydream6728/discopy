import random
from collections import Counter
from itertools import product

import pytest

from discopy import monoidal
from discopy.catalytic import Leaf, Planar, leaves, strategy

SHAPES = ((1, 1), (1, 2), (2, 1), (0, 1), (1, 0))
x = monoidal.Ty('x')


def walks(walk, state, k, normal=True):
    """ Every walk of ``k`` leaves from a state, in normal form or not. """
    if not k:
        yield ()
        return
    left, right = state
    width = max(left, 0) + right
    for i, leaf in enumerate(walk.leaves):
        offsets = walk.offsets(state, leaf.dom) if normal\
            else range(width - leaf.dom + 1)
        for offset in offsets:
            after = (offset, width - offset - leaf.dom + leaf.cod)
            for rest in walks(walk, after, k - 1, normal):
                yield ((i, offset), ) + rest


def diagram(walk, width, steps):
    result, wires = monoidal.Diagram.id(x ** width), width
    for i, offset in steps:
        leaf = walk.leaves[i]
        box = monoidal.Box(f"f{i}", x ** leaf.dom, x ** leaf.cod)
        result = result >> x ** offset @ box @ x ** (
            wires - offset - leaf.dom)
        wires += leaf.cod - leaf.dom
    return result


def orbit(term):
    """ The least string of the drawings a drawing interchanges to. """
    seen, todo = {str(term)}, [term]
    while todo:
        current = todo.pop()
        for i, left in product(range(len(current) - 1), (False, True)):
            for a, b in ((i, i + 1), (i + 1, i)):
                try:
                    other = current.interchange(a, b, left=left)
                except Exception:  # pylint: disable=broad-except
                    continue
                if str(other) not in seen:
                    seen.add(str(other))
                    todo.append(other)
    return min(seen)


@pytest.mark.parametrize("width,k", [(1, 2), (2, 2), (1, 3), (2, 3)])
def test_normal_form_is_one_walk_per_diagram(width, k):
    walk = Planar(tuple(Leaf("box", *shape) for shape in SHAPES))
    start = (-1, width)

    def classes(normal):
        return Counter(orbit(diagram(walk, width, steps))
                       for steps in walks(walk, start, k, normal))

    normal, every = classes(True), classes(False)
    assert set(normal) == set(every)
    assert all(count == 1 for count in normal.values())


def test_counts_of_one_box():
    walk = Planar((Leaf("box", 1, 1), ), z=1.)
    assert [walk.exactly(k, 2, 2) for k in range(5)] == [1, 2, 3, 4, 5]


def test_catalytic_fixed_point():
    walk = Planar(tuple(Leaf("box", *shape) for shape in SHAPES), z=.05)
    total = walk.total(1, 1)
    series = sum(walk.z ** k * walk.exactly(k, 1, 1) for k in range(60))
    assert total == pytest.approx(series, rel=1e-9)


def test_sampler_is_exact():
    walk = Planar(tuple(Leaf("box", *shape) for shape in SHAPES[:3]),
                  y=.2, width=12)
    k, rng, n = 2, random.Random(0), 20000
    exact = Counter()
    for m in range(walk.width + 1):
        for steps in walks(walk, (-1, m), k):
            exact[m, steps] += walk.y ** m * walk.y ** (
                m + sum(walk.leaves[i].cod - walk.leaves[i].dom
                        for i, _ in steps))
    draws = Counter()
    for _ in range(n):
        m, steps = walk.sample(rng, count=k)
        draws[m, tuple(steps)] += 1
    total = sum(exact.values())
    assert total == pytest.approx(walk.exactly(k), rel=1e-6)
    distance = sum(abs(draws[key] / n - weight / total)
                   for key, weight in exact.items()) / 2
    assert distance < .03


def test_leaves():
    from discopy import rigid
    names = {leaf.name for _, leaf in leaves(rigid.Diagram)}
    assert names == {"box", "wiring"}


@pytest.mark.parametrize("module", ["monoidal", "braided", "rigid",
                                    "pivotal", "biclosed"])
def test_strategy(module):
    from importlib import import_module
    from hypothesis import HealthCheck, given, settings, strategies as st
    category = import_module(f"discopy.{module}")
    a = category.Ty('a')

    @settings(max_examples=10, deadline=None, database=None,
              suppress_health_check=list(HealthCheck))
    @given(st.data())
    def check(data):
        term = data.draw(strategy(category.Diagram, a, a @ a))
        assert (term.dom, term.cod) == (a, a @ a)
        data.draw(strategy(category.Diagram))
    check()
