import random
from collections import Counter
from itertools import product

import pytest

from discopy import compact, frobenius, markov, symmetric
from discopy.plumbing import Plumbing, Sampler, kind_of, line, recency


def scans(plumbing, points):
    """
    Every way to scan a line, as its wires, each a sorted tuple of points,
    and the crossings it pays: the recency of each wire it joins.
    """
    def go(i, state, pools, wires, crossings):
        if i == len(points):
            if state == plumbing.start:
                yield tuple(sorted(map(tuple, wires))), crossings
            return
        for move, _, after in plumbing.transitions(state, points[i]):
            pool, status, _ = move
            for j in range(1 if pool is None else state[pool]):
                new_pools = [list(p) for p in pools]
                new_wires = [list(w) for w in wires]
                if pool is None:
                    wire = len(new_wires)
                    new_wires.append([])
                else:
                    wire = new_pools[pool].pop(len(pools[pool]) - 1 - j)
                new_wires[wire].append(i)
                if status is not None:
                    new_pools[status].append(wire)
                yield from go(i + 1, after, new_pools, new_wires,
                              crossings + j)
    yield from go(0, plumbing.start, [[] for _ in plumbing.start], [], 0)


def crossings(pairs):
    return sum(a < c < b < d for (a, b), (c, d) in product(pairs, repeat=2))


def inversions(pairs):
    port = line((len(pairs), len(pairs)), [])
    target = [port[b] for _, b in sorted(pairs)]
    return sum(i < j and target[i] > target[j]
               for i, j in product(range(len(target)), repeat=2))


LINES = [points for n in range(1, 7)
         for points in product((True, False), repeat=n)]


@pytest.mark.parametrize("kind,acyclic", [
    ("bijection", True), ("bijection", False), ("matching", False),
    ("function", True), ("function", False), ("cospan", False)])
def test_scan_is_a_bijection(kind, acyclic):
    plumbing = Plumbing(kind, q=.5, acyclic=acyclic)
    for points in LINES:
        found = list(scans(plumbing, points))
        assert len({wires for wires, _ in found}) == len(found)
        assert sum(.5 ** c for _, c in found)\
            == pytest.approx(plumbing.count(points))


def test_matching_energy_is_crossings():
    for points in LINES:
        for wires, energy in scans(Plumbing("matching"), points):
            assert energy == crossings(wires)


def test_permutation_energy_is_inversions():
    for n in range(1, 6):
        points = n * (True, ) + n * (False, )
        found = list(scans(Plumbing("bijection", acyclic=True), points))
        for wires, energy in found:
            assert energy == inversions(wires)


def test_touchard_riordan():
    q = .5
    assert Plumbing("matching", q=q).count(6 * (True, ))\
        == pytest.approx(5 + 6 * q + 3 * q ** 2 + q ** 3)
    assert Plumbing("matching", q=0).count(8 * (True, )) == 14


def test_planar_matchings_nest():
    for points in LINES:
        for wires, energy in scans(Plumbing("matching", q=0), points):
            if energy == 0:
                assert crossings(wires) == 0


@pytest.mark.parametrize("kind", ["bijection", "matching", "cospan"])
def test_sampler_is_exact(kind):
    sampler = Sampler(Plumbing(kind, q=.5), x=.3, max_boxes=1,
                      shapes=((1, 1), (0, 2)), loops=0)
    weights = Counter()
    for k, shapes in [(0, [])] + [(1, [s]) for s in sampler.shapes]:
        points = (True, ) + tuple(
            p for m, n in shapes for p in m * (False, ) + n * (True, ))\
            + (False, )
        for wires, energy in scans(sampler.plumbing, points):
            weights[tuple(shapes), wires] += sampler.x ** k * .5 ** energy
    assert sum(weights.values()) == pytest.approx(sampler.total(1, 1))
    rng, n = random.Random(0), 20000
    draws = Counter()
    for _ in range(n):
        shapes, wires = sampler.sample(rng, 1, 1)
        draws[tuple(shapes), tuple(sorted(map(tuple, wires)))] += 1
    total = sum(weights.values())
    distance = sum(abs(draws[key] / n - weight / total)
                   for key, weight in weights.items()) / 2
    assert distance < .02 and set(draws) <= set(weights)


def test_recency_extremes():
    assert recency(5, 0., .999) == 0
    assert recency(5, 1., .999) == 4


@pytest.mark.parametrize("module", [symmetric, compact, markov, frobenius])
def test_strategy(module):
    from hypothesis import HealthCheck, given, settings, strategies as st
    x = module.Ty('x')
    sampler = Sampler(Plumbing(kind_of(module.Diagram)), max_boxes=3)\
        .tuned(2.)

    @settings(max_examples=10, deadline=None, database=None,
              suppress_health_check=list(HealthCheck))
    @given(st.data())
    def check(data):
        diagram = data.draw(sampler.strategy(module.Diagram, x, x @ x))
        assert (diagram.dom, diagram.cod) == (x, x @ x)
    check()


def test_no_legs_is_one_structure_less():
    for points in LINES:
        assert Plumbing("cospan", legs=0).count(points)\
            == pytest.approx(Plumbing("matching").count(points))
        for acyclic in (True, False):
            assert Plumbing("function", legs=0, acyclic=acyclic).count(
                points) == pytest.approx(Plumbing(
                    "bijection", acyclic=acyclic).count(points))


@pytest.mark.parametrize("kind", ["cospan", "function"])
def test_legs_count_generators(kind):
    def energy(wires):
        return sum(abs(len(wire) - 2) for wire in wires)
    for points in LINES:
        assert Plumbing(kind, q=1, legs=.5).count(points)\
            == pytest.approx(sum(.5 ** energy(wires) for wires, _ in scans(
                Plumbing(kind, q=1), points)))


@pytest.mark.parametrize("kind", ["bijection", "matching", "cospan"])
def test_free_boundaries_are_exact(kind):
    sampler = Sampler(Plumbing(kind, q=.5, legs=.3), max_boxes=1,
                      shapes=((1, 1), (0, 2)), loops=0, boundary=.15)
    total = sampler.total(None, None)
    exact = {(m, n): sampler.boundary ** (m + n) * sampler.total(m, n)
             for m in range(sampler.width) for n in range(sampler.width)}
    assert sum(exact.values()) == pytest.approx(total, rel=1e-3)
    rng, draws = random.Random(0), Counter()
    for _ in range(20000):
        walk = sampler.walk(rng, None, None)
        draws[tuple(walk.widths)] += 1
    distance = sum(abs(draws[key] / 20000 - weight / total)
                   for key, weight in exact.items()) / 2
    assert distance < .02
