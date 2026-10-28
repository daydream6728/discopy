"""
Catalytic Boltzmann samplers: diagrams with unbounded boundaries, the width
of a diagram a catalytic variable of its generating function rather than an
index of finitely many sorts.

A planar diagram, i.e. of a monoidal category or one with more structure
but no symmetry, is read top to bottom as a walk: each step a leaf of the
grammar of its category, see :func:`discopy.boltzmann.compile`, i.e. a box,
a braid, a twist, an evaluation or a block of planar wiring, at an offset.
The walk is in normal form when each leaf takes a wire at or right of the
outputs of the one before, i.e. when it could not be applied before it on
its left, so that a diagram up to interchange is one walk, see
:meth:`Planar.offsets`. Its state is the pair ``(left, right)`` of the wires
left of the outputs of the last leaf and from them on, and the generating
function :math:`G(u, v) = \\sum z^k u^{left} v^{right}` of the walks from a
domain of ``m`` wires is the solution of the linear catalytic equation

.. math::
    G(u, v) = v^m + z \\sum_{a, b} \\beta_{a b} K_{a b}[G](u, v)

where :math:`\\beta_{a b}` weighs the leaves of shape ``a -> b`` and
:math:`K_{a b}` sends a state to the states each offset of such a leaf leads
to: :math:`u^l v^b (v^{r - a + 1} - u^{r - a + 1}) / (v - u)` for the leaves
right of the last outputs, a divided difference, and the offsets that
straddle them besides. The planar diagrams up to interchange grow
exponentially, as the planar maps they are, so that the equation has a
solution below a positive ``z``: the walks of drawings would grow
factorially with the orders of independent leaves.

A sampler needs the completion :math:`F(s)` of each state, the total weight
of the walks from it, the end of a free codomain weighing ``y`` per wire:

.. math::
    F(s) = y^{|s|} + z \\sum_{s \\to s'} \\beta F(s')

solved as a sparse linear system on the states of at most
:attr:`Planar.width` wires, a numerical truncation, below its singularity,
the reciprocal of the spectral radius of the transfer matrix, see
:attr:`Planar.singularity`.
Conditioned on ``k`` leaves, ``z`` cancels out and :math:`F_k = A^k F_0` is a
power of the transfer matrix.

A free domain of ``m`` wires is drawn with weight :math:`y^m F(m)`.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Leaf
    Planar

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        leaves
        planar
        strategy
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from functools import cached_property, lru_cache
from random import Random

import numpy as np
from scipy import sparse

from discopy import boltzmann, plumbing
from discopy.abc import MonoidalCategory
from discopy.grammar import cfg
from discopy.unification import MISMATCH, Unifier, atoms_of

State = tuple[int, int]
"""
The wires left of the outputs of the last leaf, ``-1`` before the first,
and the wires from them on.
"""


@dataclass(frozen=True)
class Leaf:
    """
    A leaf of a walk: its shape ``dom -> cod`` and its weight.

    Parameters:
        name : The name of the rule it applies, ``"box"`` for a generator.
        dom : Its number of inputs.
        cod : Its number of outputs.
        weight : Its weight :math:`\\beta`.
    """
    name: str
    dom: int
    cod: int
    weight: float = 1.


@dataclass
class Planar:
    """
    The catalytic Boltzmann sampler of planar walks, see the module.

    Parameters:
        leaves : The leaves a walk takes its steps from.
        z : The weight of a leaf.
        y : The weight of a wire of a free domain or codomain.
        width : The most wires of a state, a numerical truncation.

    Example
    -------
    The monoidal diagrams of one box ``1 -> 1`` up to interchange are its
    sequences: from a domain of two wires, the box can be anywhere at first,
    then at the wire it last wrote or right of it.

    >>> walk = Planar((Leaf("box", 1, 1), ), z=1.)
    >>> [walk.exactly(k, 2, 2) for k in range(4)]
    [1.0, 2.0, 3.0, 4.0]
    """
    leaves: tuple[Leaf, ...]
    z: float = .1
    y: float = .3
    width: int = 24
    cache: dict = field(default_factory=dict, repr=False, compare=False)

    @cached_property
    def states(self) -> list[State]:
        """ The states of at most :attr:`width` wires, the starts first. """
        return [(-1, right) for right in range(self.width + 1)] + [
            (left, right) for left in range(self.width + 1)
            for right in range(self.width + 1 - left)]

    @cached_property
    def index(self) -> dict[State, int]:
        """ The index of each state in :attr:`states`. """
        return {state: i for i, state in enumerate(self.states)}

    @staticmethod
    def offsets(state: State, dom: int) -> range:
        """
        The offsets of a leaf with ``dom`` inputs in normal form: any at the
        start, then those that take a wire at or right of the outputs of the
        last leaf, or right of them for a leaf with no input.

        >>> list(Planar.offsets((1, 2), 1)), list(Planar.offsets((1, 2), 0))
        ([1, 2], [2, 3])
        """
        left, right = state
        low = 0 if left < 0 else max(0, left - dom + 1)
        return range(low, max(left, 0) + right - dom + 1)

    def after(self, state: State, i: int, offset: int) -> State:
        """ The state after the ``i``-th leaf at an offset. """
        leaf = self.leaves[i]
        return offset, max(state[0], 0) + state[1] - offset\
            - leaf.dom + leaf.cod

    def steps(self, state: State):
        """ The leaf, offset and next state of each step from a state. """
        for i, leaf in enumerate(self.leaves):
            for offset in self.offsets(state, leaf.dom):
                after = self.after(state, i, offset)
                if sum(after) <= self.width:
                    yield i, offset, after

    @cached_property
    def matrix(self) -> sparse.csr_matrix:
        """
        The transfer matrix :math:`A`, the weight :math:`\\beta` of the steps
        from each state to each other.
        """
        rows, cols, data = [], [], []
        for state in self.states:
            for i, _, after in self.steps(state):
                rows.append(self.index[state])
                cols.append(self.index[after])
                data.append(self.leaves[i].weight)
        size = len(self.states)
        return sparse.csr_matrix((data, (rows, cols)), shape=(size, size))

    def stops(self, cod: int | None) -> np.ndarray:
        """ The weight of ending at each state: ``y`` per wire if free. """
        widths = np.array([max(left, 0) + right
                           for left, right in self.states])
        return self.y ** widths if cod is None\
            else (widths == cod).astype(float)

    @cached_property
    def singularity(self) -> float:
        """
        The least ``z`` at which the walks of at most :attr:`width` wires
        have no Boltzmann distribution, the reciprocal of the spectral
        radius of :attr:`matrix`, which bounds that of every width below.
        """
        # pylint: disable-next=import-outside-toplevel  # only to tune
        from scipy.sparse.linalg import eigs
        radius = abs(eigs(self.matrix, k=1, which="LM",
                          return_eigenvectors=False)[0])
        return math.inf if radius < 1e-12 else 1 / radius

    def completion(self, cod: int | None = None) -> np.ndarray:
        """
        The completion :math:`F = y^{|s|} + z A F` of each state, the
        solution of a sparse linear system, raising :class:`ValueError` at
        or above the :attr:`singularity`.
        """
        # pylint: disable-next=import-outside-toplevel  # only to solve
        from scipy.sparse.linalg import spsolve
        if self.z >= self.singularity:
            raise ValueError(f"No Boltzmann distribution at z = {self.z}.")
        key = "completion", cod
        if key not in self.cache:
            identity = sparse.identity(len(self.states), format="csc")
            self.cache[key] = spsolve(
                (identity - self.z * self.matrix).tocsc(), self.stops(cod))
        return self.cache[key]

    def powers(self, cod: int | None, count: int) -> np.ndarray:
        """ The completions :math:`F_k = A^k F_0` of ``k = count`` leaves. """
        key = "powers", cod
        if key not in self.cache:
            self.cache[key] = [self.stops(cod)]
        powers = self.cache[key]
        while len(powers) <= count:
            powers.append(self.matrix @ powers[-1])
        return powers[count]

    def starts(self, values: np.ndarray, dom: int | None) -> dict:
        """ The weight of each width of the domain, ``y`` per wire if free. """
        widths = range(self.width + 1) if dom is None else [dom]
        return {m: (self.y ** m if dom is None else 1.)
                * values[self.index[-1, m]] for m in widths}

    def total(self, dom: int | None = None, cod: int | None = None) -> float:
        """ The total weight of the walks from ``dom`` to ``cod`` wires. """
        return float(sum(self.starts(self.completion(cod), dom).values()))

    def exactly(self, count: int, dom: int | None = None,
                cod: int | None = None) -> float:
        """ The total weight of the walks with exactly ``count`` leaves. """
        return float(sum(self.starts(self.powers(cod, count), dom).values()))

    def expected(self, dom: int | None = None, cod: int | None = None,
                 step: float = 1e-4) -> float:
        """
        The expected number of leaves, the derivative of the logarithm of
        :meth:`total` in that of :attr:`z`.

        >>> walk = Planar((Leaf("box", 1, 1), Leaf("box", 1, 2),
        ...                Leaf("box", 2, 1)), y=.2)
        >>> walk = walk.tuned(3.)
        >>> round(walk.expected(), 3)
        3.0
        """
        up, down = (replace(self, z=self.z * math.exp(sign * step), cache={})
                    .total(dom, cod) for sign in (1, -1))
        return (math.log(up) - math.log(down)) / (2 * step)

    def tuned(self, mean: float, dom: int | None = None,
              cod: int | None = None, steps: int = 40) -> Planar:
        """
        The walk with ``mean`` leaves on average, by bisection on ``z``
        below the :attr:`singularity`.
        """
        low, high = 0., min(1., self.singularity)
        for _ in range(steps):
            middle = (low + high) / 2
            too_many = replace(self, z=middle, cache={}).expected(
                dom, cod) > mean
            low, high = (low, middle) if too_many else (middle, high)
        return replace(self, z=low, cache={})

    def sample(self, random: Random, dom: int | None = None,
               cod: int | None = None, count: int | None = None
               ) -> tuple[int, list[tuple[int, int]]]:
        """
        The width of the domain and the steps of a walk, each the index of
        a leaf and its offset: Boltzmann distributed at :attr:`z`, or
        conditioned on exactly ``count`` leaves, in which ``z`` cancels.
        """
        def values(left):
            return self.completion(cod) if count is None\
                else self.powers(cod, left)

        factor = self.z if count is None else 1.
        width = choose(random, self.starts(values(count or 0), dom))
        state, steps, stops = (-1, width), [], self.stops(cod)
        while count is None or len(steps) < count:
            ahead = values(None if count is None else count - len(steps) - 1)
            ways = {} if count is not None\
                else {None: stops[self.index[state]]}
            ways |= {(i, offset): factor * self.leaves[i].weight
                     * ahead[self.index[after]]
                     for i, offset, after in self.steps(state)}
            way = choose(random, ways)
            if way is None:
                break
            steps.append(way)
            state = self.after(state, *way)
        return width, steps

    def strategy(  # pylint: disable=too-many-arguments  # bounds
            self, category: type, dom=None, cod=None, *,
            max_leaves: int = 6, attempts: int = 100):
        """
        The :mod:`hypothesis` strategy of the diagrams of ``category`` from
        ``dom`` to ``cod``, free when not given: a number of leaves drawn
        uniformly up to ``max_leaves``, a walk conditioned on it, typed by
        unification, see :func:`build`, from a generator seeded by every
        draw of Hypothesis, as :meth:`discopy.plumbing.Sampler.strategy`.
        """
        # pylint: disable-next=import-outside-toplevel  # it imports this
        from hypothesis import reject, strategies as st
        spec = boltzmann.compile(category)
        productions = [production for production, _ in leaves(category)]

        @st.composite
        def diagrams(draw):
            seed = draw(st.integers(0, 2 ** 64 - 1))
            palette = spec.palette(dom, cod, draw=draw)
            random = Random(repr((seed, palette)))
            count = random.randint(0, max_leaves)
            sides = tuple(None if side is None else len(side)
                          for side in (dom, cod))
            if not self.exactly(count, *sides):
                return reject()
            for _ in range(attempts):
                width, steps = self.sample(random, *sides, count=count)
                term = build(category, spec, productions, width, steps,
                             (dom, cod), random, palette)
                if term is not None:
                    return term()
            return reject()

        return diagrams()


def choose(random: Random, weights: dict):
    """ A key of ``weights`` drawn in proportion to its value. """
    draw, total = random.random() * sum(weights.values()), 0.
    for key, weight in weights.items():
        total += weight
        if draw < total:
            return key
    return key  # pylint: disable=undefined-loop-variable  # rounding


def leaves(category: type, structure: float = .3) -> list[tuple]:
    """
    The leaves of the grammar of a category, see
    :func:`discopy.boltzmann.compile`: its productions with no morphism
    premise but the identity, each with its :class:`Leaf`, a generator
    weighing one and any other ``structure``.

    >>> from discopy import braided
    >>> sorted({leaf.name for _, leaf in leaves(braided.Diagram)})
    ['box', 'braiding', 'inverse_braiding']
    """
    spec = boltzmann.compile(category)
    return [(production, Leaf(production.name, *spec.shape_of[production.cod],
                              1. if production.name == "box" else structure))
            for production in spec.productions
            if not production.dom
            and production.name not in ("ax", "identity", "any")
            and production.cod in spec.shape_of]


def build(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals  # noqa: E501
        # a walk, its boundary and how to type it
        category: type, spec, productions: list, width: int, steps: list,
        sides: tuple, random: Random, palette: tuple):
    """
    How to build the diagram of a walk, or ``None`` when it cannot be typed:
    each wire a placeholder, each leaf derived by
    :meth:`discopy.boltzmann.Specification.derive` between the wires it
    takes and fresh ones, unified with ``sides`` when given, and each box a
    generator with a fresh identifier.
    """
    ob = category.ob

    def generator(dom, cod):
        return category.box_factory(f"f_{random.getrandbits(128):032x}",
                                    dom, cod)

    def tensor(atoms):
        return ob().tensor(*atoms)

    unifier = Unifier(category, random, palette, generator)
    wire = boltzmann.wire(category)
    wires = atoms_of(unifier.fresh(wire ** width))
    start, layers = list(wires), []
    try:
        if sides[0] is not None:
            unifier.unify(sides[0], tensor(wires))
        for i, offset in steps:
            production = productions[i]
            a, b = spec.shape_of[production.cod]
            outputs = atoms_of(unifier.fresh(wire ** b))
            leaf = spec.derive(cfg.Tree(production),
                               tensor(wires[offset:offset + a]),
                               tensor(outputs), unifier)
            if leaf is None:
                return None
            layers.append((wires[:offset], leaf, wires[offset + a:]))
            wires = wires[:offset] + outputs + wires[offset + a:]
        if sides[1] is not None:
            unifier.unify(sides[1], tensor(wires))
    except MISMATCH:
        return None

    def term():
        result = category.id(unifier.resolve(tensor(start)))
        for left, leaf, right in layers:
            result = result >> unifier.resolve(tensor(left)) @ leaf()\
                @ unifier.resolve(tensor(right))
        return result
    return term


@lru_cache(maxsize=None)
def planar(category: type, structure: float = .3, ports: float = 3.,
           max_leaves: int = 6) -> Planar:
    """
    The :class:`Planar` walk of a category, its free sides tuned to
    ``ports`` wires with half of ``max_leaves`` leaves, once.
    """
    walk = Planar(tuple(leaf for _, leaf in leaves(category, structure)))
    low, high = 0., 1.
    for _ in range(30):
        middle = (low + high) / 2
        trial = replace(walk, y=middle, cache={})
        k, step = max_leaves // 2, 1e-4
        up, down = (replace(trial, y=middle * math.exp(sign * step),
                            cache={}).exactly(k) for sign in (1, -1))
        mean = (math.log(up) - math.log(down)) / (2 * step)\
            if up > 0 and down > 0 else math.inf
        low, high = (low, middle) if mean > ports else (middle, high)
    return replace(walk, y=low, cache={})


def strategy(category: type, dom=None, cod=None, **params):
    """
    The catalytic strategy of the diagrams of a category with unbounded
    boundaries: its plumbing when it has some, see
    :func:`discopy.plumbing.strategy`, its :func:`planar` walk otherwise.

    >>> from hypothesis import find
    >>> from discopy.rigid import Ty, Diagram
    >>> x = Ty('x')
    >>> diagram = find(strategy(Diagram, x, x), lambda d: len(d) > 2)
    >>> assert (diagram.dom, diagram.cod) == (x, x)
    """
    if plumbing.kind_of(category) is not None:
        return plumbing.strategy(category, dom, cod)
    if not issubclass(category, MonoidalCategory):
        raise NotImplementedError(f"No catalytic sampler for {category}.")
    return planar(category, **params).strategy(category, dom, cod)
