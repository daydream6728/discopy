# -*- coding: utf-8 -*-

from itertools import permutations
from random import Random

import pytest

from discopy import compact, rigid, symmetric
from discopy.wiring import count, diagram, matching, noncrossing

KINDS = {"permutation": symmetric, "brauer": compact, "planar": rigid}


def atoms(module, m, pairs):
    """ The types of the points of a wiring, one name per pair. """
    result = [None] * (m + max([q for _, q in pairs], default=-1) + 1 - m)
    for i, (p, q) in enumerate(pairs):
        a = module.Ty(f"a{i}")
        result[p], result[q] = (a, a.r) if q < m\
            else (a, a.l) if p >= m else (a, a)
    return result


@pytest.mark.parametrize("kind", list(KINDS))
def test_counts(kind):
    """ The wirings drawn are as many as counted, and none is the identity.
    """
    random = Random(0)
    for m, n in [(0, 2), (1, 1), (2, 2), (1, 3), (3, 3)]:
        others = count(kind, m, n) - (m == n)
        if not others:
            with pytest.raises(ValueError):
                matching(kind, m, n, random)
            continue
        drawn = {tuple(matching(kind, m, n, random)) for _ in range(500)}
        assert len(drawn) == others


@pytest.mark.parametrize("kind", list(KINDS))
def test_types(kind):
    """ The diagram of every wiring has the types of its points. """
    module, random = KINDS[kind], Random(0)
    for m in range(4):
        for n in range(4):
            if count(kind, m, n) < 2:
                continue
            for _ in range(10):
                pairs = matching(kind, m, n, random)
                typed = atoms(module, m, pairs)
                result = diagram(module.Diagram, kind, m, pairs, typed)
                assert result.dom == module.Ty().tensor(*typed[:m])
                assert result.cod == module.Ty().tensor(*typed[m:])


def test_noncrossing():
    """ The noncrossing matchings of 2k points are the Catalan number. """
    assert [len(noncrossing(tuple(range(2 * k)))) for k in range(5)]\
        == [1, 1, 2, 5, 14]


def test_permutations():
    """ Every permutation of three wires is drawn. """
    random = Random(0)
    drawn = {tuple(q - 3 for _, q in matching("permutation", 3, 3, random))
             for _ in range(300)}
    assert drawn == set(permutations(range(3))) - {(0, 1, 2)}
