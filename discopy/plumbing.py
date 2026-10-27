"""
Plumbing: the wiring of a diagram as one morphism of the free category on
objects alone, sampled apart from its boxes with a weight ``q`` per crossing.

A diagram of a traced symmetric, compact, Markov or hypergraph category on a
signature is a set of boxes together with its plumbing: a morphism of the
free such category on objects alone, from the domain and the outputs of the
boxes to the inputs of the boxes and the codomain, i.e. a partition of the
ports into wires, see :class:`discopy.hypergraph.Hypergraph`:

* a bijection in a traced symmetric category, from producers to consumers;
* a Brauer diagram in a compact category, any perfect matching;
* a finite function in a Markov category, from consumers to producers;
* a cospan of finite functions in a hypergraph category, any partition.

The Temperley-Lieb diagrams are the Brauer diagrams with no crossing.

The ports are put on a line around the diagram, see :func:`line`, and each
wire is drawn as an arc above it. A wire crosses another when they could be
swapped, i.e. when the point closing one could have joined the other, and
the energy of plumbing is its number of crossings: the inversions of a
permutation, the crossings of a Brauer diagram, so that the plumbing with
none is planar, the identity or a Temperley-Lieb diagram, at ``q = 0``.

The line is read left to right with a transfer matrix on the number of wires
left open of each status, see :meth:`Plumbing.moves`: a wire is chosen among
the ``h`` open ones that a point can join with weight :math:`[h]_q = 1 + q +
\\dots + q^{h - 1}`, the ``j``-th newest with weight ``q ** j``, crossing the
``j`` open wires opened after it, e.g. a permutation is Mallows distributed.
The plumbing of ``n`` ports at ``q < 1`` thus weighs at most
:math:`(1 - q)^{-n}` times the planar plumbing, exponential in ``n``, where
the uniform plumbing at ``q = 1`` grows factorially, so that there is no
Boltzmann distribution once boxes are free, as for closed linear lambda
terms.

A :class:`Sampler` draws boxes and plumbing together, with weight ``x`` per
box over the factorial of their number, i.e. a set of labelled boxes, and
``q`` per crossing, exactly, by the same transfer matrix extended with a
choice of the next box. Each box adds more choices of plumbing than the one
before it, so that the number of boxes is far from concentrated at any
``x``: the sampler is rather conditioned on it, see :meth:`Sampler.exactly`,
which ``x`` cancels out of, and the size of a diagram is its number of
boxes, the energy of its plumbing apart.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Plumbing
    Sampler

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        kind_of
        q_integer
        recency
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from functools import lru_cache
from random import Random

from discopy.abc import (
    HypergraphCategory, MarkovCategory, RigidCategory, SymmetricCategory,
    TracedCategory)


STATUSES = {
    "bijection": ("producer", "consumer"),
    "matching": ("open", ),
    "function": ("copied", "unrooted", "rooted"),
    "cospan": ("single", "spider"),
}
"""
The statuses of the wires left open by each kind of plumbing: a bijection
leaves open a producer waiting for its consumer, or the converse; a function
a wire with its producer and at least one consumer, one with consumers but no
producer yet, or one with its producer alone; a cospan a wire with one leg,
or with two legs or more, a spider.
"""

Move = tuple[int | None, int | None, str | None]
"""
What a point does, as the status of the open wire it joins, or ``None`` for
a new wire, the status the wire is left open with, or ``None`` when the
point closes it, and the mark it pays, ``"feedback"`` for a wire fed back,
``"legs"`` for a leg of a spider beyond the two of a plain wire, or the
missing one of a spider with one leg.
"""


def kind_of(category: type) -> str | None:
    """
    The kind of plumbing of a category, from the most structure to the least.

    >>> from discopy import symmetric, compact, markov, frobenius, monoidal
    >>> [kind_of(module.Diagram)
    ...  for module in (symmetric, compact, markov, frobenius, monoidal)]
    ['bijection', 'matching', 'function', 'cospan', None]
    """
    if issubclass(category, HypergraphCategory):
        return "cospan"
    if issubclass(category, MarkovCategory):
        return "function"
    if not issubclass(category, SymmetricCategory):
        return None
    return "matching" if issubclass(category, RigidCategory) else "bijection"


def q_integer(h: int, q: float) -> float:
    """
    The ``q``-integer :math:`[h]_q = 1 + q + \\dots + q^{h - 1}`.

    >>> q_integer(3, .5)
    1.75
    """
    return sum(q ** j for j in range(h))


def recency(h: int, q: float, draw: float, /) -> int:
    """
    The index ``j`` of the ``j``-th newest of ``h`` open wires, drawn with
    probability ``q ** j / [h]_q`` from a uniform ``draw``.

    >>> recency(3, .5, .1), recency(3, .5, .7), recency(3, 0., .99)
    (0, 1, 0)
    """
    total, scaled = 0., draw * q_integer(h, q)
    for j in range(h):
        total += q ** j
        if scaled < total:
            return j
    return h - 1


@dataclass(frozen=True)
class Plumbing:
    """
    A kind of plumbing, its weight ``q`` per crossing and whether its wires
    only go forward along the line, which makes a diagram acyclic when each
    box has its inputs before its outputs and every box comes after the
    boxes it reads from.

    Parameters:
        kind : One of ``"bijection"``, ``"matching"``, ``"function"`` and
            ``"cospan"``, see :func:`kind_of`.
        q : The weight of a crossing, ``0`` for planar plumbing.
        acyclic : Whether a consumer may only join a wire opened before it.
        feedback : The weight of a wire a consumer opens, which feeds back
            into the line, in a bijection or a function.
        legs : The weight of each leg of a spider in a cospan beyond the
            two of a wire, or missing from them, i.e. of each comultiplication
            and unit in a function: at ``legs = 0`` a cospan is a Brauer
            diagram and a function a bijection.

    Example
    -------
    The permutations of three wires, at ``q`` per inversion:

    >>> plumbing = Plumbing("bijection", q=.5, acyclic=True)
    >>> plumbing.count(3 * (True, ) + 3 * (False, ))
    2.625
    >>> 1 * (1 + .5) * (1 + .5 + .25)
    2.625
    """
    kind: str
    q: float = .5
    acyclic: bool = False
    feedback: float = 1.
    legs: float = 1.

    @property
    def start(self) -> tuple[int, ...]:
        """ The state of the line before any point: no wire open. """
        return len(STATUSES[self.kind]) * (0, )

    def moves(self, producer: bool) -> tuple[Move, ...]:
        """
        The moves of a producer or a consumer, see :data:`Move`.

        >>> Plumbing("matching").moves(True)
        ((None, 0, None), (0, None, None))
        """
        if self.kind == "matching":
            return (None, 0, None), (0, None, None)
        if self.kind == "cospan":
            return ((None, None, "legs"), (None, 0, None), (0, None, None),
                    (0, 1, None), (1, None, "legs"), (1, 1, "legs"))
        if self.kind == "bijection":
            return ((None, 0, None), (1, None, None)) if producer else (
                ((0, None, None), )
                + ((None, 1, "feedback"), ) * (not self.acyclic))
        if producer:
            return ((None, None, "legs"), (None, 2, None), (1, None, None),
                    (1, 0, None))
        return ((2, None, None), (2, 0, None), (0, None, "legs"),
                (0, 0, "legs"), *((None, 1, "feedback"), (1, 1, "legs"))
                * (not self.acyclic))

    def weight(self, move: Move, state: tuple[int, ...]) -> float:
        """ The weight of the choices of a move, see :func:`q_integer`. """
        pool, _, mark = move
        factor = 1. if mark is None else getattr(self, mark)
        choices = 1. if pool is None else q_integer(state[pool], self.q)
        return factor * choices

    def after(self, move: Move, state: tuple[int, ...]) -> tuple[int, ...]:
        """ The state after a move. """
        pool, status, _ = move
        return tuple(count - (i == pool) + (i == status)
                     for i, count in enumerate(state))

    def transitions(self, state: tuple[int, ...], producer: bool):
        """ The moves of a point with a positive weight, and their states. """
        for move in self.moves(producer):
            weight = self.weight(move, state)
            if weight > 0:
                yield move, weight, self.after(move, state)

    def count(self, points: tuple[bool, ...],
              state: tuple[int, ...] | None = None) -> float:
        """
        The total weight of the plumbing of a line of producers (``True``)
        and consumers (``False``), each plumbing weighed ``q`` per crossing.

        >>> Plumbing("matching", q=1).count(6 * (True, ))  # 5!! = 15
        15.0
        >>> Plumbing("matching", q=0).count(6 * (True, ))  # Catalan 3
        5.0
        >>> Plumbing("cospan", q=1).count(4 * (True, ))  # Bell 4
        15.0
        >>> Plumbing("function", q=1).count((True, True, False, False))  # 2^2
        4.0
        """
        states = {self.start if state is None else state: 1.}
        for producer in points:
            new: dict = {}
            for current, weight in states.items():
                for _, move_weight, after in self.transitions(
                        current, producer):
                    new[after] = new.get(after, 0.) + weight * move_weight
            states = new
        return states.get(self.start, 0.)


@dataclass
class Sampler:
    """
    The Boltzmann sampler of boxes and their plumbing: a diagram with ``k``
    boxes, each of a shape ``m -> n`` among ``shapes``, and ``c`` crossings
    has weight :math:`x^k q^c / k!`, its boxes in the order of the line.

    Each box puts its ``m`` inputs then its ``n`` outputs on the line, after
    the domain and before the codomain, so that the plumbing of an acyclic
    category only goes forward: a diagram is then counted once for each order
    of its boxes that sorts them topologically, which the weight ``1 / k!``
    makes up for when the category is traced.

    Parameters:
        plumbing : The kind of plumbing and its weight per crossing.
        x : The weight of a box.
        shapes : The shapes ``(m, n)`` of the boxes.
        min_boxes : The least number of boxes.
        max_boxes : The largest number of boxes.
        loops : The probability of each further closed loop, i.e. a spider
            with no port, of which there are geometrically many.

    Example
    -------
    >>> import random
    >>> sampler = Sampler(Plumbing("matching", q=.5), x=1., max_boxes=3)
    >>> shapes, wires = sampler.sample(random.Random(0), 1, 1)
    >>> ports = 2 + sum(m + n for m, n in shapes)
    >>> assert sorted(sum(wires, [])) == list(range(ports))
    >>> assert all(len(wire) == 2 for wire in wires)
    """
    plumbing: Plumbing
    x: float = 1.
    shapes: tuple[tuple[int, int], ...] = tuple(
        (m, n) for m in range(4) for n in range(4) if m + n)
    min_boxes: int = 0
    max_boxes: int = 8
    loops: float = .1
    cache: dict = field(default_factory=dict, repr=False, compare=False)

    def node(self, boxes: int, state: tuple, cod: tuple) -> dict:
        """
        The weight of each way on after ``boxes`` boxes: the codomain,
        ``None``, or one more box of each shape.
        """
        ways = {}
        if boxes >= self.min_boxes:
            ways[None] = self.completion(boxes, cod, state, cod, True)
        if boxes < self.max_boxes:
            for m, n in self.shapes:
                ways[m, n] = self.x / (boxes + 1) * self.completion(
                    boxes + 1, m * (False, ) + n * (True, ), state, cod, False)
        return ways

    def completion(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # noqa: E501
            # a memoised state
            self, boxes: int, rest: tuple, state: tuple, cod: tuple,
            final: bool) -> float:
        """
        The total weight of the diagrams going on from ``state``, with the
        points ``rest`` of the codomain if ``final``, else those of the last
        of ``boxes`` boxes, left on the line.
        """
        key = boxes, rest, state, cod, final
        if key not in self.cache:
            self.cache[key] = self.compute(boxes, rest, state, cod, final)
        return self.cache[key]

    def compute(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # noqa: E501
            # see completion
            self, boxes: int, rest: tuple, state: tuple, cod: tuple,
            final: bool) -> float:
        """ The value of :meth:`completion`, before it is memoised. """
        if rest:
            return sum(
                weight * self.completion(boxes, rest[1:], after, cod, final)
                for _, weight, after in self.plumbing.transitions(
                    state, rest[0]))
        if final:
            return float(state == self.plumbing.start)
        return sum(self.node(boxes, state, cod).values())

    def total(self, dom: int, cod: int) -> float:
        """ The total weight of the diagrams from ``dom`` to ``cod`` ports. """
        return self.completion(
            0, dom * (True, ), self.plumbing.start, cod * (False, ), False)

    def coefficients(self, dom: int, cod: int) -> list[float]:
        """
        The total weight of the diagrams with ``k`` boxes at ``x = 1``, for
        each ``k`` up to :attr:`max_boxes`, of which :meth:`total` is the
        polynomial in ``x`` from :attr:`min_boxes` on.
        """
        return [replace(self, x=1., min_boxes=k, max_boxes=k, cache={}).total(
            dom, cod) for k in range(self.max_boxes + 1)]

    def expected(self, dom: int, cod: int) -> float:
        """
        The expected number of boxes from ``dom`` to ``cod`` ports.

        >>> sampler = Sampler(Plumbing("cospan"), x=.1, max_boxes=2)
        >>> c = sampler.coefficients(0, 0)
        >>> mean = (.1 * c[1] + 2 * .01 * c[2])\\
        ...     / (c[0] + .1 * c[1] + .01 * c[2])
        >>> round(sampler.expected(0, 0), 6) == round(mean, 6)
        True
        """
        return self.moments(self.coefficients(dom, cod), self.x)

    def moments(self, coefficients: list[float], x: float) -> float:
        """ The mean number of boxes at ``x`` from :meth:`coefficients`. """
        terms = [c * x ** k for k, c in enumerate(coefficients)
                 if k >= self.min_boxes]
        return sum(k * t for k, t in enumerate(terms, self.min_boxes))\
            / sum(terms)

    def tuned(self, mean: float, dom: int = 1, cod: int = 1,
              steps: int = 60) -> Sampler:
        """
        The sampler whose expected number of boxes from ``dom`` to ``cod``
        ports is ``mean``, by bisection on the logarithm of ``x``.

        >>> sampler = Sampler(Plumbing("matching")).tuned(3.)
        >>> round(sampler.expected(1, 1), 3)
        3.0
        """
        coefficients, low, high = self.coefficients(dom, cod), -30., 30.
        for _ in range(steps):
            middle = (low + high) / 2
            if self.moments(coefficients, math.exp(middle)) < mean:
                low = middle
            else:
                high = middle
        return replace(self, x=math.exp((low + high) / 2), cache={})

    def sample(self, random, dom: int, cod: int) -> tuple[list, list]:
        """
        A shape for each box and the wires of the plumbing, as lists of the
        points they join, numbered along the line: the domain, the inputs then
        the outputs of each box, the codomain, see :func:`line` for their
        ports. Closed loops are empty wires.
        """
        walk = self.walk(random, dom, cod)
        return walk.shapes, walk.wires

    def walk(self, random, dom: int, cod: int) -> Walk:
        """ The walk along the line of a sample, see :meth:`sample`. """
        walk = Walk(self, random, cod * (False, ))
        walk.plumb(dom * (True, ), final=False)
        while (shape := walk.choose(walk.ways())) is not None:
            walk.shapes.append(shape)
            walk.plumb(shape[0] * (False, ) + shape[1] * (True, ), final=False)
        walk.plumb(cod * (False, ), final=True)
        while random.random() < self.loops:
            walk.wires.append([])
        return walk

    def exactly(self, boxes: int) -> Sampler:
        """
        The sampler conditioned on ``boxes`` boxes, in which ``x`` cancels
        out: a diagram is drawn with probability proportional to
        :math:`q^c` among those with that many boxes, up to their order.
        """
        key = "exactly", boxes
        if key not in self.cache:
            self.cache[key] = replace(
                self, x=1., min_boxes=boxes, max_boxes=boxes, cache={})
        return self.cache[key]

    def strategy(  # pylint: disable=too-many-arguments  # bounds
            self, category: type, dom=None, cod=None, *,
            widths: int = 2, attempts: int = 100):
        """
        The :mod:`hypothesis` strategy of the diagrams of ``category`` from
        ``dom`` to ``cod``, of width at most ``widths`` when not given: a
        number of boxes drawn by Hypothesis between :attr:`min_boxes` and
        :attr:`max_boxes`, so that it shrinks, then a sample conditioned on
        it, see :meth:`exactly`, built through
        :class:`discopy.hypergraph.Hypergraph`, its wires coloured from the
        :meth:`discopy.boltzmann.Specification.palette` and its boxes drawn
        by the ``generators`` of the category.
        """
        # pylint: disable=import-outside-toplevel  # they import this
        from hypothesis import reject, strategies as st
        from discopy import boltzmann
        from discopy.hypergraph import Hypergraph

        @st.composite
        def diagrams(draw):
            boxes = draw(st.integers(self.min_boxes, self.max_boxes))
            random = draw(st.randoms(use_true_random=True))
            palette = boltzmann.compile(category).palette(dom, cod, draw=draw)
            for _ in range(attempts):
                sides = tuple(len(side) if side is not None
                              else random.randint(0, widths)
                              for side in (dom, cod))
                if not self.exactly(boxes).total(*sides):
                    continue
                shapes, wires = self.exactly(boxes).sample(random, *sides)
                arguments = colour(category, shapes, wires, (dom, cod),
                                   sides, palette, random)
                if arguments is None:
                    continue
                inputs, outputs, box_types, wiring, spider_types = arguments
                generators = tuple(draw(category.generators(dom=x, cod=y))
                                   for x, y in box_types)
                return Hypergraph[category](
                    inputs, outputs, generators, wiring,
                    spider_types).to_diagram()
            return reject()

        return diagrams()


@dataclass
class Walk:  # pylint: disable=too-many-instance-attributes  # a walk's state
    """
    The state of a :class:`Sampler` as it walks the line: the shapes of the
    boxes so far, the wires, the open ones of each status, newest last, and
    the crossings paid so far.
    """
    sampler: Sampler
    random: Random
    cod: tuple
    shapes: list = field(default_factory=list)
    wires: list = field(default_factory=list)
    points: int = 0
    crossings: int = 0

    def __post_init__(self):
        self.state = self.sampler.plumbing.start
        self.pools: list[list[int]] = [[] for _ in self.state]

    def ways(self) -> dict:
        """ The weight of each way on, see :meth:`Sampler.node`. """
        return self.sampler.node(len(self.shapes), self.state, self.cod)

    def choose(self, weights: dict):
        """ A key of ``weights`` drawn in proportion to its value. """
        draw, total = self.random.random() * sum(weights.values()), 0.
        for key, weight in weights.items():
            total += weight
            if draw < total:
                return key
        return key  # pylint: disable=undefined-loop-variable  # rounding

    def plumb(self, points: tuple, final: bool):
        """ Plumb each point of a stretch of the line in turn. """
        boxes, plumbing = len(self.shapes), self.sampler.plumbing
        for i, producer in enumerate(points):
            weights = {
                move: weight * self.sampler.completion(
                    boxes, points[i + 1:], after, self.cod, final)
                for move, weight, after in plumbing.transitions(
                    self.state, producer)}
            self.apply(self.choose(weights))

    def apply(self, move: Move):
        """ Join the point to a wire, an open one or a new one. """
        plumbing, (pool, status, _) = self.sampler.plumbing, move
        if pool is None:
            wire = len(self.wires)
            self.wires.append([])
        else:
            opened = self.pools[pool]
            j = recency(len(opened), plumbing.q, self.random.random())
            wire = opened.pop(len(opened) - 1 - j)
            self.crossings += j
        self.wires[wire].append(self.points)
        if status is not None:
            self.pools[status].append(wire)
        self.state = plumbing.after(move, self.state)
        self.points += 1


def line(widths: tuple[int, int], shapes: list) -> list[int]:
    """
    The port at each point of the line, in the order of
    :attr:`discopy.hypergraph.Hypergraph.ports`: the line goes around the
    diagram clockwise, the domain left to right, the inputs of each box right
    to left then its outputs left to right, the codomain right to left, so
    that plumbing with no crossing is planar.

    >>> line((2, 2), [(2, 1)])
    [0, 1, 3, 2, 4, 6, 5]
    """
    result, start = list(range(widths[0])), widths[0]
    for m, n in shapes:
        result += [start + m - 1 - k for k in range(m)]
        result += [start + m + k for k in range(n)]
        start += m + n
    return result + [start + widths[1] - 1 - k for k in range(widths[1])]


def colour(  # pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments  # noqa: E501
        # a sample, its boundary and how to colour it
        category: type, shapes: list, wires: list, sides: tuple,
        widths: tuple, palette: tuple, random) -> tuple | None:
    """
    The arguments of a :class:`discopy.hypergraph.Hypergraph` but its boxes,
    their types in their place, for a sample of :class:`Sampler` with
    boundary ``sides`` of ``widths`` ports: a colour for each wire, the one
    its ports on the boundary have, else drawn from the palette, the second
    end of a cup or a cap its right adjoint. ``None`` when the boundary gives
    a wire two colours.

    >>> import random
    >>> from discopy.compact import Ty, Diagram
    >>> x = Ty('x')
    >>> dom, cod, box_types, wiring, _ = colour(
    ...     Diagram, [(0, 2)], [[0, 1], [2, 3]], (x, None), (1, 1), (x, ),
    ...     random.Random(0))
    >>> assert box_types == [(Ty(), x.r @ x)] and cod == x
    """
    ob = category.ob
    port = line(widths, shapes)
    wires = [sorted(port[p] for p in wire) for wire in wires]
    ports = [True] * widths[0] + [
        producer for m, n in shapes for producer in m * [False] + n * [True]
    ] + [False] * widths[1]
    fixed = {} if sides[0] is None else {
        i: sides[0][i:i + 1] for i in range(widths[0])}
    fixed |= {} if sides[1] is None else {
        len(ports) - widths[1] + i: sides[1][i:i + 1]
        for i in range(widths[1])}
    objects, spider_types = {}, []
    for wire in wires:
        second = wire[-1] if len(wire) == 2\
            and ports[wire[0]] == ports[wire[1]] else None
        colours = {obj.l if port == second else obj
                   for port in wire if (obj := fixed.get(port)) is not None}
        if len(colours) > 1:
            return None
        atom = colours.pop() if colours else random.choice(palette)
        spider_types.append(atom)
        objects |= {port: atom.r if port == second else atom for port in wire}
    spider = {port: i for i, wire in enumerate(wires) for port in wire}
    offsets = [widths[0]]
    for m, n in shapes:
        offsets.append(offsets[-1] + m + n)

    def tensor(points):
        return ob().tensor(*(objects[p] for p in points))

    def wiring(points):
        return tuple(spider[p] for p in points)

    inputs, outputs = range(widths[0]), range(offsets[-1], len(ports))
    box_ports = [(range(start, start + m), range(start + m, start + m + n))
                 for start, (m, n) in zip(offsets, shapes)]
    box_types = [(tensor(x), tensor(y)) for x, y in box_ports]
    wires_ = (wiring(inputs), tuple(
        (wiring(x), wiring(y)) for x, y in box_ports), wiring(outputs))
    return tensor(inputs), tensor(outputs), box_types, wires_, spider_types


def strategy(  # pylint: disable=too-many-arguments  # the knobs of a sampler
        category: type, dom=None, cod=None, *, q: float = .5,
        feedback: float = .3, legs: float = .3, max_boxes: int = 6):
    """
    The :mod:`hypothesis` strategy of the diagrams of a category with a kind
    of plumbing, see :func:`kind_of`, from ``dom`` to ``cod``: the
    :class:`Sampler` with at most ``max_boxes`` boxes, ``q`` per crossing,
    ``feedback`` per wire fed back, which is none unless the category is
    traced, and ``legs`` per spider leg beyond those of a wire, see
    :meth:`Sampler.strategy`.

    >>> from hypothesis import find
    >>> from discopy.compact import Ty, Diagram
    >>> x = Ty('x')
    >>> diagram = find(strategy(Diagram, x, x), lambda d: d.boxes)
    >>> assert (diagram.dom, diagram.cod) == (x, x)
    """
    kind = kind_of(category)
    if kind is None:
        raise NotImplementedError(f"No plumbing for {category}.")
    plumbing = Plumbing(
        kind, q=q, feedback=feedback, legs=legs,
        acyclic=not issubclass(category, TracedCategory))
    return sampler(plumbing, max_boxes).strategy(category, dom, cod)


@lru_cache(maxsize=None)
def sampler(plumbing: Plumbing, max_boxes: int) -> Sampler:
    """ The :class:`Sampler` of a plumbing, once, so that it caches. """
    return Sampler(plumbing, max_boxes=max_boxes)
