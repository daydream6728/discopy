# -*- coding: utf-8 -*-

"""
E-hypergraphs, i.e. e-graphs of diagrams with sharing.

A cartesian diagram, whose boxes are total functions, is a term with sharing,
and an e-graph gathers equal terms in e-classes of e-nodes
:cite:`WillseyEtAl21`. An e-hypergraph over a copy-discard category, e.g.
:class:`discopy.markov.Diagram`, is a diagram with sharing, i.e. a
left-monogamous acyclic :class:`discopy.hypergraph.Hypergraph`, whose boxes
are the e-nodes, with an equivalence relation on its spiders of one type,
whose classes are the e-classes. Over cartesian diagrams it is an e-graph:
it hash-conses, :meth:`EHypergraph.rebuild` closes the relation under
congruence, :meth:`EHypergraph.matches` finds a left-hand side modulo the
classes, :meth:`EHypergraph.rewrite` glues a right-hand side onto it and
:meth:`EHypergraph.saturate` does both round by round, as egg does. Its
**sections** choose a producer for each class they need: per class, where
egg's terms choose per occurrence, so that relating classes removes
sections, but :meth:`EHypergraph.extract` is a section of least tree cost.

The flags of a :class:`discopy.markov.Box` go beyond terms: equal boxes on
related inputs have related outputs only when deterministic, two samples
being independent, and a box that is not affine, e.g. a condition, is an
effect every section keeps. Equations are between cartesian diagrams, effects
being context, and equality is up to renaming the spiders.

Example
-------
Egg's own example, ``(a * 2) / 2`` with ``a`` a domain wire and each
constant a box with no input, saturates in three rounds with egg's classes,
then extracts ``a``:

>>> from discopy.markov import Ty, Box, Diagram
>>> x = Ty('x')
>>> one, two = Box('1', Ty(), x), Box('2', Ty(), x)
>>> times, divide, shift = (Box(op, x @ x, x) for op in ("*", "/", "<<"))
>>> rules = [(x @ two >> times, x @ one >> shift),
...          (times @ x >> divide, x @ divide >> times),
...          (Diagram.copy(x) >> divide, Diagram.discard(x) >> one),
...          (x @ one >> times, Diagram.id(x))]
>>> graph = Markov.from_diagram(x @ two @ two >> times @ x >> divide)
>>> rounds = list(graph.saturate(*rules))
>>> [len(set(rewritten.classes)) for rewritten in [graph] + rounds]
[4, 6, 5, 4]
>>> print(rounds[-1].extract().to_diagram())
Id(x)

The same with a ``sample``, not deterministic, so that two samples of ``p``
are two classes and ``x - x = 0`` leaves their difference as it is, while one
sample used twice cancels, then goes, being affine:

>>> zero, minus = Box('0', Ty(), x), Box('-', x @ x, x)
>>> sample = Box('sample', x, x, is_deterministic=False)
>>> cancel = (Diagram.copy(x) >> minus, Diagram.discard(x) >> zero)
>>> two = Markov.from_diagram(Diagram.copy(x) >> sample @ sample >> minus)
>>> list(two.saturate(cancel))
[]
>>> print(two.extract().to_diagram())
Copy(x) >> sample @ sample >> -
>>> *_, one = Markov.from_diagram(
...     sample >> Diagram.copy(x) >> minus).saturate(cancel)
>>> print(one.extract().to_diagram())
Copy(x, 0) @ 0

A ``condition`` is not affine, so that under ``0 * x = 0`` the output of
``0 * s`` is ``0`` but the sample ``s`` it is conditioned on stays:

>>> condition = Box('condition', x, Ty(), is_affine=False)
>>> absorb = (zero @ x >> times, Diagram.discard(x) >> zero)
>>> *_, observed = Markov.from_diagram(sample >> Diagram.copy(x)
...     >> condition @ (zero @ x >> times)).saturate(absorb)
>>> print(observed.extract().to_diagram())
0 @ sample >> x @ condition

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    EHypergraph

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        partition
        relabel
        is_pattern
        pattern
        rewire
        ast_size
"""

from collections import Counter
from collections.abc import Callable, Iterator
from functools import cached_property
from itertools import accumulate, pairwise, repeat, takewhile
from math import inf
from typing import TYPE_CHECKING, Self

from networkx import DiGraph, NetworkXUnfeasible, topological_sort
from networkx.algorithms.isomorphism import is_isomorphic

from discopy import markov, messages
from discopy.abc import HypergraphCategory, MarkovCategory, MonoidalCategory
from discopy.axioms import (
    GENERATORS, Count, Equation, Hom, Obj, Serialisable, Var, axiom)
from discopy.drawing import Node
from discopy.hypergraph import Hypergraph
from discopy.monoidal import Ty
from discopy.utils import (
    AxiomError, NamedGeneric, classproperty, factory_name, from_tree, pushout,
    resolve_factory, unbiased)

if TYPE_CHECKING:
    from hypothesis import strategies as st


def partition(n: int, pairs) -> tuple[int, ...]:
    """
    The finest partition of ``range(n)`` relating each pair, as the least
    element of the class of each element.

    >>> partition(4, [(3, 1), (1, 2)])
    (0, 1, 1, 1)
    """
    label = list(range(n))

    def find(i):
        while label[i] != i:
            label[i] = label[label[i]]
            i = label[i]
        return i

    for i, j in pairs:
        i, j = find(i), find(j)
        label[max(i, j)] = min(i, j)
    return tuple(map(find, range(n)))


def relabel(wires, label: Callable):
    """ Relabel the spiders of a :class:`hypergraph.Wiring`. """
    dom_wires, box_wires, cod_wires = wires
    return tuple(map(label, dom_wires)), tuple(
        (tuple(map(label, src)), tuple(map(label, tgt)))
        for src, tgt in box_wires), tuple(map(label, cod_wires))


def is_pattern(graph: Hypergraph) -> bool:
    """
    Whether a hypergraph is a pattern, a cartesian diagram with sharing whose
    boxes produce its codomain, see :meth:`EHypergraph.matches`.
    """
    return all(box.is_cartesian for box in graph.boxes)\
        and graph.is_left_monogamous and graph.is_acyclic\
        and not set(graph.dom_wires) & set(graph.cod_wires)


def pattern(graph: Hypergraph) -> Hypergraph:
    """
    A hypergraph without its wires from the domain straight to the codomain,
    a pattern when it is cartesian.
    """
    dom_wires, box_wires, cod_wires = graph.wires
    kept = [k for k, s in enumerate(cod_wires) if s not in dom_wires]
    return type(graph)(
        graph.dom, type(graph.cod)().tensor(*(graph.cod[k] for k in kept)),
        graph.boxes, (dom_wires, box_wires, tuple(cod_wires[k] for k in kept)))


def rewire(graph: Hypergraph, i: int, j: int) -> Hypergraph:
    """
    A hypergraph in a topological order with the ``i``-th input of its boxes
    read from the ``j``-th other spider of its type before it: a pattern that
    a matcher missing a constraint finds where the original is.

    >>> from discopy.markov import Ty, Box
    >>> x = Ty('x')
    >>> f, g = Box('f', x, x), Box('g', x @ x, x)
    >>> graph = (x @ f >> g).to_hypergraph()
    >>> graph.box_wires, rewire(graph, 1, 0).box_wires
    ((((1,), (2,)), ((0, 2), (3,))), (((1,), (2,)), ((1, 2), (3,))))
    """
    graph = graph.topological_order()
    wires, types = list(graph.flat_wires), graph.spider_types
    inputs = [p for p, node in enumerate(graph.ports) if node.kind == "dom"]
    port = inputs[i % len(inputs)] if inputs else 0
    others = [s for s in dict.fromkeys(wires[:port])
              if s != wires[port] and types[s] == types[wires[port]]]
    if not others:
        return graph
    wires[port] = others[j % len(others)]
    return type(graph)(
        graph.dom, graph.cod, graph.boxes, graph.rebracket(wires))


def ast_size(_box) -> int:
    """ The cost of a box in egg's ``AstSize``: one, whatever the box. """
    return 1


class EHypergraph[category](
        MonoidalCategory["Ty", "EHypergraph"], NamedGeneric, Serialisable):
    """
    An e-hypergraph over a copy-discard ``category``, see
    :mod:`discopy.ehypergraph`.

    Parameters:
        graph : A left-monogamous acyclic hypergraph, its boxes the e-nodes.
        classes : The least spider related to each spider, the e-classes,
            the identity relation by default.

    Example
    -------
    Rewriting ``a * 2``, the boxes 0 and 1 from the spider 0 to the spider 2,
    into ``a << 1``, extraction takes the least producer of least cost unless
    multiplication costs more than a shift:

    >>> from discopy.markov import Ty, Box
    >>> x = Ty('x')
    >>> one, two = Box('1', Ty(), x), Box('2', Ty(), x)
    >>> times, shift = Box('*', x @ x, x), Box('<<', x @ x, x)
    >>> left, right = x @ two >> times, x @ one >> shift
    >>> graph = Markov.from_diagram(left).rewrite(
    ...     (0, 1), (0, ), (2, ), right.to_hypergraph())
    >>> assert graph.sections() == [
    ...     left.to_hypergraph(), right.to_hypergraph()]
    >>> assert graph.extract() == left.to_hypergraph()
    >>> cost = lambda box: 2 if box == times else 1
    >>> assert graph.extract(box_cost=cost) == right.to_hypergraph()
    """
    ob = classproperty(lambda cls: cls.category.ob)

    def __init__(
            self, graph: Hypergraph, classes: tuple[int, ...] | None = None):
        if not isinstance(self.category, type)\
                or not issubclass(self.category, markov.Diagram):
            raise AxiomError(messages.NOT_MARKOV.format(factory_name(
                type(self))))
        if not graph.is_left_monogamous or not graph.is_acyclic:
            raise AxiomError(messages.NOT_SHARING.format(graph))
        n = graph.n_spiders
        classes = tuple(range(n) if classes is None else classes)
        if len(classes) != n or any(
                graph.spider_types[s] != graph.spider_types[c]
                for s, c in enumerate(classes)):
            raise AxiomError(messages.TYPE_ERROR.format(
                f"a class of one type for each of {n} spiders", classes))
        self.graph, self.classes = graph, partition(n, enumerate(classes))

    dom = property(lambda self: self.graph.dom)
    cod = property(lambda self: self.graph.cod)

    @classmethod
    def from_diagram(cls, diagram) -> Self:
        """
        The e-hypergraph of a diagram, rebuilt so that equal deterministic
        boxes on equal inputs are one class, as egg hash-conses a term.

        >>> from discopy.markov import Ty, Box
        >>> x = Ty('x')
        >>> two, divide = Box('2', Ty(), x), Box('/', x @ x, x)
        >>> Markov.from_diagram(two @ two >> divide).classes
        (0, 0, 2)
        """
        return cls(Hypergraph[cls.category].from_diagram(diagram)).rebuild()

    @classmethod
    def id(cls, dom=None) -> Self:
        return cls(Hypergraph[cls.category].id(dom))

    def carry(self, graph: Hypergraph, wires, pairs) -> Self:
        """
        The e-hypergraph of a hypergraph built from some wires, with pairs of
        their spiders related, carried to the spiders it relabels them to.
        """
        dom_wires, box_wires, cod_wires = wires
        label = dict(zip(dom_wires + sum((
            src + tgt for src, tgt in box_wires), ()) + cod_wires,
            graph.flat_wires))
        return type(self)(graph, partition(graph.n_spiders, (
            (label[s], label[t]) for s, t in pairs)))

    @unbiased
    def then(self, other: Self) -> Self:
        """ Composition, the relations carried along the pushout. """
        left, right = pushout(
            self.graph.n_spiders, other.graph.n_spiders,
            self.graph.cod_wires, other.graph.dom_wires)
        (dom_wires, box_wires, _), (_, others, cod_wires) = relabel(
            self.graph.wires, left.get), relabel(other.graph.wires, right.get)
        pairs = [(left[s], left[c]) for s, c in enumerate(self.classes)] + [
            (right[s], right[c]) for s, c in enumerate(other.classes)]
        return self.carry(self.graph >> other.graph, (
            dom_wires, box_wires + others, cod_wires), pairs)

    @unbiased
    def tensor(self, other: Self) -> Self:
        """ Tensor, the disjoint union of the hypergraphs and relations. """
        n = self.graph.n_spiders
        wires = tuple(map(lambda x, y: x + y, self.graph.wires, relabel(
            other.graph.wires, n.__add__)))
        pairs = list(enumerate(self.classes)) + [
            (n + s, n + c) for s, c in enumerate(other.classes)]
        return self.carry(self.graph @ other.graph, wires, pairs)

    def merge(self, *spiders: int) -> Self:
        """ Relate spiders of one type, i.e. state that they are equal. """
        pairs = list(enumerate(self.classes)) + list(zip(spiders, spiders[1:]))
        return type(self)(self.graph, partition(self.graph.n_spiders, pairs))

    def pair(self, i: int, j: int) -> tuple[int, ...]:
        """ The ``i``-th spider and the ``j``-th of its type, for the laws. """
        if not self.graph.n_spiders:
            return ()
        types = self.graph.spider_types
        first = i % len(types)
        same = [s for s, typ in enumerate(types) if typ == types[first]]
        return first, same[j % len(same)]

    def twice(self) -> Self:
        """ Two copies side by side on related inputs, rebuilt. """
        result, n = self @ self, len(self.dom)
        for k in range(n):
            result = result.merge(*result.graph.dom_wires[k::n])
        return result.rebuild()

    def inputs(self, box: int) -> tuple[int, ...]:
        """ The classes a box reads, given by its index. """
        return tuple(self.classes[s] for s in self.graph.box_wires[box][0])

    def box_of(self, port: int) -> int | None:
        """ The box of an output port, :obj:`None` for a domain position. """
        node = self.graph.ports[port]
        return node.depth if node.kind == "cod" else None

    def reads(self, port: int) -> tuple[int, ...]:
        """ The classes the producer at a port reads, none for an input. """
        box = self.box_of(port)
        return () if box is None else self.inputs(box)

    def rebuild(self) -> Self:
        """
        The congruence closure, egg's rebuild: it relates the outputs of equal
        deterministic boxes on related inputs, but not those of two samples.
        """
        graph, classes = self.graph, self.classes
        while True:
            first, pairs = {}, list(enumerate(classes))
            for box, (src, tgt) in zip(graph.boxes, graph.box_wires):
                if box.is_deterministic:
                    key = box, tuple(classes[s] for s in src)
                    pairs += zip(first.setdefault(key, tgt), tgt)
            if partition(graph.n_spiders, pairs) == classes:
                return type(self)(graph, classes)
            classes = partition(graph.n_spiders, pairs)

    def add(self, box, inputs: tuple[int, ...]) -> tuple[Self, tuple]:
        """
        Add a box reading some spiders, egg's add, and return its outputs, or
        those of an equal deterministic box on the same classes: not a sample.
        """
        key = tuple(self.classes[s] for s in inputs)
        for j, other in enumerate(self.graph.boxes):
            if box.is_deterministic and other == box and self.inputs(j) == key:
                return self, self.graph.box_wires[j][1]
        graph, n = self.graph, self.graph.n_spiders
        outputs = tuple(range(n, n + len(box.cod)))
        wires = (graph.dom_wires, graph.box_wires + (
            (tuple(inputs), outputs), ), graph.cod_wires)
        result = self.carry(type(graph)(
            graph.dom, graph.cod, graph.boxes + (box, ), wires), wires,
            enumerate(self.classes))
        return result, result.graph.box_wires[-1][1]

    def assert_equation(self, region: tuple[int, ...], dom: tuple, cod: tuple,
                        rhs: Hypergraph):
        """ Raise unless :meth:`rewrite` can enter an equation, see there. """
        graph, classes = self.graph, self.classes
        for box in tuple(graph.boxes[j] for j in region) + rhs.boxes:
            if not box.is_cartesian:
                raise AxiomError(messages.NOT_CARTESIAN.format(box))
        if not rhs.is_left_monogamous or not rhs.is_acyclic:
            raise AxiomError(messages.NOT_SHARING.format(rhs))

        def fits(s, t):
            return not rhs.spider_wires[t][1] if s is None\
                else graph.spider_types[s] == rhs.spider_types[t]

        if (len(dom), len(cod)) != (len(rhs.dom), len(rhs.cod)) or not all(
                map(fits, dom + cod, rhs.dom_wires + rhs.cod_wires)):
            raise AxiomError(messages.NOT_A_BOUNDARY.format(rhs, dom, cod))
        reached, todo = {classes[s] for s in dom if s is not None}, set(region)
        while fired := {j for j in todo if set(self.inputs(j)) <= reached}:
            todo -= fired
            reached |= {
                classes[s] for j in fired for s in graph.box_wires[j][1]}
        if todo or any(classes[s] not in reached for s in cod):
            raise AxiomError(messages.NOT_A_REGION.format(region, dom, cod))

    def rewrite(self, region: tuple[int, ...], dom: tuple, cod: tuple,
                rhs: Hypergraph) -> Self:
        """
        State that a region, the boxes computing the spiders ``cod`` from
        ``dom``, :obj:`None` where ``rhs`` does not read, equals a hypergraph
        ``rhs``: glue it onto ``dom``, hash-consing its boxes with :meth:`add`,
        and relate ``cod`` to its outputs. The region stays: an e-graph never
        deletes, a section may. It raises :class:`AxiomError`, see
        :meth:`assert_equation`, when a box of either side is not cartesian,
        an effect being context, when the boundaries have other types, when
        ``rhs`` is not a diagram with sharing, or when the region cannot fire
        in some order from ``dom`` to ``cod``.
        """
        dom, cod = tuple(dom), tuple(cod)
        self.assert_equation(region, dom, cod, rhs)
        rhs, result, image = rhs.topological_order(), self, {}
        image.update(zip(rhs.dom_wires, dom))
        for box, (src, tgt) in zip(rhs.boxes, rhs.box_wires):
            result, outputs = result.add(box, tuple(image[s] for s in src))
            image.update(zip(tgt, outputs))
        for spider, target in zip(cod, rhs.cod_wires):
            result = result.merge(spider, image[target])
        return result

    def matches(self, lhs: Hypergraph) -> list[tuple[tuple, tuple, tuple]]:
        """
        The matches of a pattern modulo the classes, egg's e-matching: a
        cartesian diagram with sharing whose boxes produce its codomain, as a
        variable alone would match anything. A match binds each box of ``lhs``
        to an equal box, flags included, each spider to one class, and is
        ``(region, dom, cod)``, the boxes and the least spiders of the classes
        bound, :obj:`None` where ``lhs`` does not read, so that
        ``rewrite(*match, rhs)`` applies a rule. The boxes are bound top-down,
        from the codomain up, with :meth:`bind`.

        >>> from discopy.markov import Ty, Box, Diagram
        >>> x = Ty('x')
        >>> f, g = Box('f', x, x), Box('g', x @ x, x)
        >>> graph = Markov.from_diagram(Diagram.copy(x) >> f @ f >> g)
        >>> graph.matches((Diagram.copy(x) >> g).to_hypergraph())
        [((2,), (1,), (3,))]
        """
        if not is_pattern(lhs):
            raise AxiomError(messages.NOT_A_PATTERN.format(lhs))
        lhs, partial = lhs.topological_order(), [({}, ())]
        for j in reversed(range(len(lhs.boxes))):
            partial = [(new, region + (h, )) for env, region in partial
                       for h, new in self.bind(lhs, j, env)]
        return list(dict.fromkeys((
            tuple(sorted(set(region))), tuple(map(env.get, lhs.dom_wires)),
            tuple(map(env.get, lhs.cod_wires))) for env, region in partial))

    def bind(self, lhs: Hypergraph, j: int, env: dict) -> Iterator[tuple]:
        """
        The boxes the ``j``-th box of a pattern binds to, given a binding of
        its spiders to classes, each with the binding it extends to: an equal
        box, flags included, with its ports on the classes bound, among the
        producers of the class an output is bound to, or any if none is.
        """
        (src, tgt), classes = lhs.box_wires[j], self.classes
        k = next((k for k, s in enumerate(tgt) if s in env), None)
        hosts = range(len(self.graph.boxes)) if k is None else [
            node.depth for node in map(
                self.graph.ports.__getitem__, self.producers[env[tgt[k]]])
            if node.kind == "cod" and node.i == k]
        for h in hosts:
            new = dict(env)
            if self.graph.boxes[h] == lhs.boxes[j] and all(
                    new.setdefault(p, classes[s]) == classes[s] for p, s in
                    zip(src + tgt, sum(self.graph.box_wires[h], ()))):
                yield h, new

    def step(self, rules: list[tuple[Hypergraph, Hypergraph]]) -> Self:
        """
        A round of egg's schedule under a list of pairs ``(lhs, rhs)`` of
        hypergraphs: every match as the round begins rewritten, then rebuilt.
        """
        result = self
        for match, rhs in [(match, rhs) for lhs, rhs in rules
                           for match in self.matches(lhs)]:
            result = result.rewrite(*match, rhs)
        return result.rebuild()

    def saturate(self, *rules) -> Iterator[Self]:
        """
        Saturate under some rules, yielding each :meth:`step` from the rebuilt
        e-hypergraph that adds a box or relates two classes, stopping at the
        first that does neither. A rule is a pair ``(lhs, rhs)`` of cartesian
        diagrams of one type, ``lhs`` a pattern and ``rhs`` reading only the
        inputs ``lhs`` reads, as in egg, else it raises :class:`AxiomError` as
        it is called. Rules need not saturate: cut the rounds.
        """
        def reads(graph):
            return {k for k, s in enumerate(graph.dom_wires)
                    if graph.spider_wires[s][1]}

        def size(graph):
            return len(graph.graph.boxes), len(set(graph.classes))

        pairs = []
        for lhs, rhs in rules:
            left, right = lhs.to_hypergraph(), rhs.to_hypergraph()
            if (lhs.dom, lhs.cod) != (rhs.dom, rhs.cod) or not is_pattern(
                    left) or not all(box.is_cartesian for box in right.boxes)\
                    or not reads(right) <= reads(left):
                raise AxiomError(messages.NOT_A_RULE.format(lhs, rhs))
            pairs.append((left, right))
        rounds = pairwise(accumulate(
            repeat(pairs), type(self).step, initial=self.rebuild()))
        return (new for _, new in takewhile(
            lambda pair: size(pair[0]) != size(pair[1]), rounds))

    @cached_property
    def producers(self) -> dict[int, tuple[int, ...]]:
        """ The producer ports of each class, domain positions first. """
        result: dict[int, list[int]] = {}
        for spider, (ports, _) in enumerate(self.graph.spider_wires):
            result.setdefault(self.classes[spider], []).extend(ports)
        return {q: tuple(sorted(ports)) for q, ports in result.items()}

    def roots(self) -> tuple[int, ...]:
        """
        The boxes every section keeps, not affine, but the later of two equal
        deterministic ones on related inputs: a constraint holds once.
        """
        found = {}
        for j, box in enumerate(self.graph.boxes):
            if not box.is_affine:
                key = (box, self.inputs(j)) if box.is_deterministic else j
                found.setdefault(key, j)
        return tuple(found.values())

    def needs(self) -> tuple[int, ...]:
        """ The classes every section needs, of the codomain and roots. """
        return tuple(self.classes[s] for s in self.graph.cod_wires) + tuple(
            q for j in self.roots() for q in self.inputs(j))

    def section(self, choice: dict[int, int]) -> Hypergraph:
        """
        The section of a choice of a producer port for each class it needs:
        the roots and the boxes it chooses in a causal order, a spider for each
        class and a fresh one, discarded, for each producer not chosen. It
        raises :class:`AxiomError` on a cycle.
        """
        graph, classes = self.graph, self.classes
        dependencies, todo = DiGraph(), list(self.needs())
        dependencies.add_nodes_from(todo)
        while todo:
            q = todo.pop()
            todo += [r for r in self.reads(choice[q]) if r not in dependencies]
            dependencies.add_edges_from((r, q) for r in self.reads(choice[q]))
        try:
            position = {q: i for i, q in enumerate(
                topological_sort(dependencies))}
        except NetworkXUnfeasible as error:
            raise AxiomError(messages.NOT_ACYCLIC.format(choice)) from error
        kept = sorted(set(self.roots()) | {
            j for j in map(self.box_of, map(choice.__getitem__, position))
            if j is not None}, key=lambda j: (max(
                map(position.__getitem__, self.inputs(j)), default=-1), j))
        ports = [min(producers) for producers, _ in graph.spider_wires]

        def produce(wires):
            return tuple(
                classes[s] if choice.get(classes[s]) == ports[s]
                and classes[s] in position else graph.n_spiders + s
                for s in wires)

        wires = produce(graph.dom_wires), tuple(
            (self.inputs(j), produce(graph.box_wires[j][1])) for j in kept), \
            tuple(classes[s] for s in graph.cod_wires)
        return type(graph)(
            graph.dom, graph.cod, tuple(graph.boxes[j] for j in kept), wires)

    def sections(self) -> list[Hypergraph]:
        """ The section of every acyclic choice, by brute force. """
        producers, result = self.producers, []

        def extend(choice, todo):
            if not todo:
                try:
                    result.append(self.section(choice))
                except AxiomError:
                    pass
                return
            q, rest = todo[0], todo[1:]
            for port in (choice[q], ) if q in choice else producers[q]:
                reads = () if q in choice else self.reads(port)
                extend({**choice, q: port}, rest + reads)

        extend({}, self.needs())
        return result

    def tree_cost(self, box: int, costs: dict[int, float],
                  box_cost: Callable = ast_size) -> float:
        """ The tree cost of a box, given those of the classes it reads. """
        return box_cost(self.graph.boxes[box]) + sum(
            costs[q] for q in self.inputs(box))

    def relax(self, box_cost: Callable = ast_size, input_cost: float = 1
              ) -> tuple[dict[int, float], dict[int, int]]:
        """
        The least tree cost of each class by Bellman-Ford relaxation, with its
        least producer of least cost: exact and acyclic when every box costs
        at least one. A box costs ``box_cost(box)``, one by default as in
        egg's ``AstSize``, and a domain position ``input_cost``.
        """
        producers = self.producers
        costs = dict.fromkeys(producers, inf)

        def weight(port):
            box = self.box_of(port)
            return input_cost if box is None\
                else self.tree_cost(box, costs, box_cost)

        while lower := {q: min(map(weight, ports)) for q, ports in producers
                        .items() if min(map(weight, ports)) < costs[q]}:
            costs.update(lower)
        return costs, {q: next(p for p in ports if weight(p) == costs[q])
                       for q, ports in producers.items()}

    def cost(self, box_cost: Callable = ast_size, input_cost: float = 1
             ) -> float:
        """ The least tree cost of a section, of its codomain and roots. """
        costs, _ = self.relax(box_cost, input_cost)
        return sum(costs[self.classes[s]] for s in self.graph.cod_wires) + sum(
            self.tree_cost(j, costs, box_cost) for j in self.roots())

    def extract(self, box_cost: Callable = ast_size, input_cost: float = 1
                ) -> Hypergraph:
        """ A section of least tree cost, egg's extraction. """
        return self.section(self.relax(box_cost, input_cost)[1])

    def to_graph(self) -> DiGraph:
        """ The labelled graph of the hypergraph, with a node per class. """
        graph = self.graph.to_graph()
        for spider, (label, obj) in enumerate(zip(
                self.classes, self.graph.spider_types)):
            graph.add_node(("class", label), box="class")
            graph.add_edge(("class", label), Node("spider", i=spider, obj=obj))
        return graph

    def __eq__(self, other) -> bool:
        if not isinstance(other, EHypergraph) or self.graph != other.graph:
            return False
        return is_isomorphic(
            self.to_graph(), other.to_graph(), lambda x, y: x == y)

    def __hash__(self) -> int:
        sizes = sorted(Counter(self.classes).values())
        return hash((self.graph, tuple(sizes)))

    def __repr__(self) -> str:
        return factory_name(type(self))\
            + f"(graph={self.graph!r}, classes={self.classes!r})"

    def to_tree(self) -> dict:
        """ Serialise the e-hypergraph, with the name of its category. """
        return {'factory': factory_name(EHypergraph),
                'category': factory_name(self.category),
                'graph': self.graph.to_tree(), 'classes': list(self.classes)}

    @classmethod
    def from_tree(cls, tree: dict) -> Self:
        """ Decode a serialised e-hypergraph, see :meth:`to_tree`. """
        factory = cls[resolve_factory(tree['category'])]
        return factory(from_tree(tree['graph']), tuple(tree['classes']))

    @classmethod
    def strategy(cls, effects: bool = True, max_merges: int = 3, **params
                 ) -> "st.SearchStrategy[EHypergraph]":
        """
        Generate an acyclic hypergraph, its types and boxes named after two
        generators, some boxes not deterministic or not affine if ``effects``,
        then up to ``max_merges`` merges; ``params`` go to the hypergraph.
        """
        from hypothesis import strategies as st

        category = cls.category
        if category is None or not issubclass(category, MarkovCategory)\
                or issubclass(category, HypergraphCategory):
            raise NotImplementedError(
                f"No strategy implemented for {factory_name(cls)}.")
        words = st.lists(st.sampled_from(GENERATORS[:2]), max_size=2)
        graphs = Hypergraph[category].strategy(**{
            "types": words.map(lambda word: category.ob(*word)),
            "acyclic": True, "max_scalars": 0, **params})
        effect = st.booleans() if effects else st.just(False)
        numbers = st.integers(0, 9)

        @st.composite
        def ehypergraphs(draw):
            graph = draw(graphs)
            boxes = tuple(category.box_factory(
                draw(st.sampled_from(GENERATORS[:2])), box.dom, box.cod,
                is_deterministic=not draw(effect), is_affine=not draw(effect))
                for box in graph.boxes)
            result = cls(type(graph)(graph.dom, graph.cod, boxes, graph.wires))
            for _ in range(draw(st.integers(0, max_merges))):
                result = result.merge(
                    *result.pair(draw(numbers), draw(numbers)))
            return result

        return ehypergraphs()

    dagger_involution = MonoidalCategory.dagger_involution.inapplicable(
        messages.SHARING_HAS_NO_DAGGER)
    dagger_contravariance = MonoidalCategory.dagger_contravariance\
        .inapplicable(messages.SHARING_HAS_NO_DAGGER)
    dagger_monoidality = MonoidalCategory.dagger_monoidality.inapplicable(
        messages.SHARING_HAS_NO_DAGGER)

    @axiom
    def graph_functoriality[
            A: Obj[Ty], B: Obj[Ty], C: Obj[Ty], D: Obj[Ty], E: Obj[Ty]](
            cls, f: Hom[Self, A, B], g: Hom[Self, B, C], h: Hom[Self, D, E]
    ) -> Equation[Hypergraph]:
        """ The hypergraph of an e-hypergraph is a strict monoidal functor. """
        return Equation(((f >> g) @ h).graph, (f.graph >> g.graph) @ h.graph)

    @axiom
    def merge_equivalence[I: Count, J: Count, K: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J],
            k: Var[int, K]) -> Equation[tuple[Self, ...]]:
        """ Merging is reflexive, symmetric and transitive. """
        if not graph.graph.n_spiders:
            return Equation((), ())
        (s, t), (_, u) = graph.pair(i, j), graph.pair(i, k)
        chained = graph.merge(s, t).merge(t, u)
        return Equation(
            (graph.merge(s, s), graph.merge(s, t), chained.merge(s, u)),
            (graph, graph.merge(t, s), chained))

    @axiom
    def rebuild_closure[I: Count, J: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J]
    ) -> Equation[Self]:
        """
        Rebuilding is idempotent, keeps the equations it had and is confluent,
        closing before an equation or only after.
        """
        pair = graph.pair(i, j)
        closed = graph.merge(*pair).rebuild()
        return Equation(closed, closed.rebuild(), closed.merge(*pair),
                        graph.rebuild().merge(*pair).rebuild())

    @axiom
    def rebuild_minimality(cls, graph: Self) -> Equation[tuple[int, ...]]:
        """ A closure is generated by the relation and congruent outputs. """
        closed, first, pairs = graph.rebuild(), {}, list(enumerate(
            graph.classes))
        for spider, (ports, _) in enumerate(closed.graph.spider_wires):
            node, j = closed.graph.ports[min(ports)], closed.box_of(min(ports))
            if j is not None and closed.graph.boxes[j].is_deterministic:
                key = closed.classes[spider], closed.graph.boxes[j], node.i
                pairs.append((first.setdefault(key, spider), spider))
        return Equation(partition(len(closed.classes), pairs), closed.classes)

    @axiom
    def congruence[A: Obj[Ty], B: Obj[Ty], C: Obj[Ty]](
            cls, f: Hom[Self, A, B], g: Hom[Self, B, C]
    ) -> Equation[tuple[bool, ...]]:
        """
        Relating the inputs of two copies relates two outputs exactly when
        every box they depend on is deterministic.
        """
        composite = f >> g
        graph, m = composite.graph, len(g.cod)
        twice = type(f)(graph).twice()
        cod, classes = twice.graph.cod_wires, twice.classes

        def determined(spider):
            box = composite.box_of(min(graph.spider_wires[spider][0]))
            return box is None or graph.boxes[box].is_deterministic and all(
                map(determined, graph.box_wires[box][0]))

        return Equation(
            tuple(classes[cod[k]] == classes[cod[m + k]] for k in range(m)),
            tuple(map(determined, graph.cod_wires)))

    @axiom
    def extraction_soundness(cls, graph: Self) -> Equation[tuple]:
        """
        What is extracted is a section, decodes to a diagram encoding back to
        it, and is what its own e-hypergraph extracts.
        """
        extracted = graph.extract()
        return Equation((extracted in graph.sections(), extracted), (
            True, extracted.to_diagram().to_hypergraph()), (
            True, type(graph)(extracted).extract()))

    @axiom
    def extraction_optimality(cls, graph: Self) -> Equation[int]:
        """ What is extracted costs :meth:`cost`, no section costs less. """
        return Equation(type(graph)(graph.extract()).cost(), graph.cost(), min(
            type(graph)(section).cost() for section in graph.sections()))

    @axiom
    def effects_kept(cls, graph: Self) -> Equation[bool]:
        """
        Every section keeps every box that is not affine, once for equal
        deterministic ones on related inputs, checked on two copies.
        """
        def effects(boxes, inputs):
            pairs = [(box, src) for box, src in zip(boxes, inputs)
                     if not box.is_affine]
            hard = {pair for pair in pairs if pair[0].is_deterministic}
            return len(hard), Counter(
                box for box, _ in pairs if not box.is_deterministic)

        twice = graph @ graph
        expected = effects(twice.graph.boxes, map(
            twice.inputs, range(len(twice.graph.boxes))))
        return Equation(all(expected == effects(
            section.boxes, (src for src, _ in section.box_wires))
            for section in twice.sections()), True)

    @axiom
    def rewrite_identity(cls, graph: Self) -> Equation[Self]:
        """ Rewriting a rebuilt e-hypergraph into itself changes nothing. """
        rebuilt, (dom_wires, _, cod_wires) = graph.rebuild(), graph.graph.wires
        return Equation(rebuilt.rewrite(
            tuple(range(len(graph.graph.boxes))),
            tuple(rebuilt.classes[s] for s in dom_wires), cod_wires,
            graph.graph), rebuilt)

    @axiom
    def extraction_rewrite[A: Obj[Ty], B: Obj[Ty]](
            cls, f: Hom[Self, A, B], g: Hom[Self, A, B]) -> Equation[bool]:
        """
        Rewriting ``f`` into what ``g`` extracts costs no more than either.
        """
        rewritten = f.rewrite(
            tuple(range(len(f.graph.boxes))), f.graph.dom_wires,
            f.graph.cod_wires, g.extract())
        return Equation(type(f)(rewritten.extract()).cost() <= min(
            f.cost(), g.cost()), True)

    @axiom
    def matching_completeness[A: Obj[Ty], B: Obj[Ty], C: Obj[Ty]](
            cls, f: Hom[Self, A, B], g: Hom[Self, B, C]) -> Equation[bool]:
        """
        Matching is complete modulo the classes: binding the boxes of ``g`` to
        two copies of ``f >> g`` in turn is a match of its pattern.
        """
        composite, lhs = f >> g, pattern(g.graph)
        n, m, twice = len(composite.graph.boxes), len(f.graph.boxes), \
            composite.twice()
        region = [m + j + n * (j % 2) for j in range(len(lhs.boxes))]
        image = {s: twice.classes[t] for j, (src, tgt) in zip(
            region, lhs.box_wires) for s, t in zip(
            src + tgt, sum(twice.graph.box_wires[j], ()))}
        match = tuple(sorted(region)), tuple(map(
            image.get, lhs.dom_wires)), tuple(map(image.get, lhs.cod_wires))
        return Equation(match in twice.matches(lhs), True)

    @axiom
    def matching_soundness[A: Obj[Ty], B: Obj[Ty], C: Obj[Ty], I: Count,
                           J: Count](
            cls, f: Hom[Self, A, B], g: Hom[Self, B, C], i: Var[int, I],
            j: Var[int, J]) -> Equation[bool]:
        """
        Matching is sound, flags included: in ``(f >> c) @ g``, with ``c`` the
        boxes of ``g`` made cartesian, rewriting a match into its own pattern
        changes nothing, for the pattern of ``c`` and for it rewired, see
        :func:`rewire`, which a matcher missing a constraint finds in ``c``
        and one blind to flags in ``g``.
        """
        graph, factory = g.graph, cls.category.box_factory
        graph = type(graph)(graph.dom, graph.cod, tuple(factory(
            box.name, box.dom, box.cod) for box in graph.boxes), graph.wires)
        composite = ((f >> type(g)(graph)) @ g).rebuild()
        lhs = pattern(graph)
        return Equation(all(
            composite.rewrite(*match, lhs) == composite
            for lhs in (lhs, rewire(lhs, i, j))
            for match in composite.matches(lhs)), True)

    @axiom
    def saturation(cls, graph: Self) -> Equation[bool]:
        """
        A round after saturation changes nothing: once some rules stop, the
        result is rebuilt and no match of them changes it, for the rules
        equating the boxes of a type, then also each box with a fresh one.
        """
        boxes, fresh = dict.fromkeys(graph.graph.boxes), GENERATORS[2]
        same = [(b, c) for b in boxes for c in boxes
                if (b.dom, b.cod) == (c.dom, c.cod)]
        renamed = [(b, cls.category.box_factory(fresh, b.dom, b.cod))
                   for b in boxes]

        def saturated(rules):
            *_, last = graph.rebuild(), *graph.saturate(*rules)
            return last == last.rebuild() and all(
                last.rewrite(*match, rhs.to_hypergraph()) == last
                for lhs, rhs in rules
                for match in last.matches(lhs.to_hypergraph()))

        return Equation(saturated(same), saturated(same + renamed), True)

    rewrite_identity = rewrite_identity.weaken(effects=False)
    extraction_rewrite = extraction_rewrite.weaken(effects=False)
    matching_completeness = matching_completeness.weaken(effects=False)
    saturation = saturation.weaken(effects=False)


Markov = EHypergraph[markov.Diagram]
