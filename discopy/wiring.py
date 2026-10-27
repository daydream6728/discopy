"""
Wirings in normal form: the morphisms of the free symmetric, compact or
planar rigid category on objects alone, i.e. permutations, `Brauer diagrams
<https://en.wikipedia.org/wiki/Brauer_algebra>`_ and `Temperley-Lieb
diagrams <https://en.wikipedia.org/wiki/Temperley%E2%80%93Lieb_algebra>`_,
up to their closed loops.

A wiring from ``m`` wires to ``n`` is a perfect matching of ``m + n``
points, the inputs ``0, ..., m - 1`` and the outputs ``m, ..., m + n - 1``:
a pair of an input and an output is a through wire, one of two inputs a
cup and one of two outputs a cap, noncrossing around the boundary when the
wiring is planar. It is the one representative of every composite of
swaps, cups and caps that the equations of the category identify, e.g. a
snake or two swaps in a row, so that :mod:`discopy.boltzmann` draws the
wiring of a diagram in one block rather than derive it, see
:meth:`discopy.boltzmann.Specification.connect`.

Summary
-------

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        kind_of
        count
        noncrossing
        matching
        diagram
        brauer
        planar
"""

from __future__ import annotations

import math
from functools import lru_cache

from discopy.abc import SymmetricCategory


WIRES = {
    "permutation": {"ax", "braiding", "inverse_braiding"},
    "planar": {"ax", "unit", "counit"},
    "brauer": {"ax", "unit", "counit", "braiding", "inverse_braiding"},
}
"""
The rules each kind of wiring replaces: a block of wiring in normal form,
see :func:`count`, rather than the derivations of its swaps, cups and caps,
so that no derivation spends its size on wiring the equations erase.
"""


def kind_of(category: type, names: list[str]) -> str | None:
    """
    The kind of wiring a free category draws in blocks, from the rules its
    terms are derived by: ``"permutation"`` with swaps, ``"planar"`` with
    cups and caps, ``"brauer"`` with both, ``None`` with neither or when its
    braids are not swaps, e.g. a braided category, whose braids stay boxes.

    >>> from discopy import compact, rigid, braided
    >>> kind_of(compact.Diagram, ["braiding", "counit", "unit"])
    'brauer'
    >>> kind_of(rigid.Diagram, ["counit", "unit"])
    'planar'
    >>> kind_of(braided.Diagram, ["braiding"]) is None
    True
    """
    symmetric = issubclass(category, SymmetricCategory)\
        and "braiding" in names
    if "unit" in names and "counit" in names:
        return "brauer" if symmetric else "planar"
    return "permutation" if symmetric else None


def count(kind: str | None, m: int, n: int) -> int:
    """
    The number of wirings in normal form from ``m`` wires to ``n``: the
    permutations, the perfect matchings of ``m + n`` points, i.e. Brauer
    diagrams, or the noncrossing ones, i.e. Temperley-Lieb diagrams.

    >>> [count(kind, 2, 2) for kind in ("permutation", "brauer", "planar")]
    [2, 3, 2]
    """
    if kind == "permutation":
        return math.factorial(n) if m == n else 0
    if kind is None or (m + n) % 2:
        return 0
    k = (m + n) // 2
    if kind == "brauer":
        return math.prod(range(1, 2 * k, 2))
    return math.comb(2 * k, k) // (k + 1)


@lru_cache(maxsize=None)
def noncrossing(points: tuple) -> tuple:
    """ The noncrossing perfect matchings of points around a circle. """
    if not points:
        return ((), )
    first, rest = points[0], points[1:]
    return tuple(
        ((first, rest[i]), ) + inner + outer
        for i in range(0, len(rest), 2)
        for inner in noncrossing(rest[:i])
        for outer in noncrossing(rest[i + 1:]))


def matching(kind: str, m: int, n: int, random) -> list[tuple[int, int]]:
    """
    A wiring in normal form drawn uniformly but for the identity, which is
    the production ``identity``, as the pairs of its points: its inputs
    ``0, ..., m - 1`` and its outputs ``m, ..., m + n - 1``, sorted within
    each pair.
    """
    identity = [(i, m + i) for i in range(m)] if m == n else None
    if count(kind, m, n) <= (identity is not None):
        raise ValueError(f"No {kind} wiring from {m} to {n} but the identity.")
    while True:
        pairs = draw_matching(kind, m, n, random)
        if pairs != identity:
            return pairs


def draw_matching(kind: str, m: int, n: int, random) -> list[tuple]:
    """ A wiring in normal form drawn uniformly, see :func:`matching`. """
    if kind == "permutation":
        targets = list(range(m, m + n))
        random.shuffle(targets)
        return list(zip(range(m), targets))
    if kind == "brauer":
        points = list(range(m + n))
        random.shuffle(points)
        return sorted(tuple(sorted(points[i:i + 2]))
                      for i in range(0, m + n, 2))
    circle = tuple(range(m)) + tuple(reversed(range(m, m + n)))
    return sorted(tuple(sorted(pair))
                  for pair in random.choice(noncrossing(circle)))


def diagram(category: type, kind: str, m: int, pairs: list, atoms: list):
    """
    The diagram of a wiring in normal form, its points typed by ``atoms``,
    see :func:`planar` and :func:`brauer`.

    >>> from discopy.rigid import Ty, Diagram
    >>> x = Ty('x')
    >>> snake = diagram(Diagram, "planar", 1, [(0, 1)], [x, x])
    >>> assert snake == Diagram.id(x)
    """
    return (planar if kind == "planar" else brauer)(category, m, pairs, atoms)


def typer(category: type, atoms: list):
    """ The object of the points of a wiring, typed by ``atoms``. """
    ob = category.typeparams()[0]
    return lambda points: ob().tensor(*(atoms[p] for p in points))


def brauer(category: type, m: int, pairs: list, atoms: list):
    """
    The diagram of a wiring of a symmetric category: the inputs permuted so
    that the through wires come first, in the order of their outputs, then
    the cups of the inputs, the caps of the outputs, and the outputs
    permuted back into their order.
    """
    tensor = typer(category, atoms)
    through = sorted((q, p) for p, q in pairs if p < m <= q)
    cups = [pair for pair in pairs if pair[1] < m]
    caps = [pair for pair in pairs if pair[0] >= m]
    order = [p for _, p in through] + [p for pair in cups for p in pair]
    outputs = [q for q, _ in through] + [q for pair in caps for q in pair]
    middle = category.id(tensor([p for _, p in through]))
    return category.permutation(order, tensor(range(m)))\
        >> middle.tensor(*(category.cups(atoms[p], atoms[q])
                           for p, q in cups))\
        >> middle.tensor(*(category.caps(atoms[p], atoms[q])
                           for p, q in caps))\
        >> category.permutation(
            [outputs.index(q) for q in sorted(outputs)], tensor(outputs))


def planar(category: type, m: int, pairs: list, atoms: list):
    """
    The diagram of a planar wiring: the cups of its inputs, innermost
    first, then the caps of its outputs, outermost first, the through wires
    in between in order.
    """
    tensor, links = typer(category, atoms), set(pairs)

    def adjacent(points):
        return next((i for i, pair in enumerate(zip(points, points[1:]))
                     if pair in links), None)

    state, result = list(range(m)), category.id(tensor(range(m)))
    while (k := adjacent(state)) is not None:
        result = result >> tensor(state[:k]) @ category.cups(
            atoms[state[k]], atoms[state[k + 1]]) @ tensor(state[k + 2:])
        del state[k:k + 2]
    outputs, steps = sorted(q for pair in links for q in pair if q >= m), []
    while (k := adjacent(outputs)) is not None:
        steps.append((k, outputs[k], outputs[k + 1]))
        del outputs[k:k + 2]
    for k, p, q in reversed(steps):
        result = result >> tensor(outputs[:k]) @ category.caps(
            atoms[p], atoms[q]) @ tensor(outputs[k:])
        outputs[k:k] = [p, q]
    return result
