# -*- coding: utf-8 -*-

"""
E-hypergraphs, i.e. e-graphs of diagrams with sharing.

A cartesian diagram, whose boxes are total functions, is a term with sharing:
copying a wire shares a subterm, discarding it drops one. An e-graph gathers
equal terms in e-classes, each the set of its e-nodes, the operations on
e-classes that compute it :cite:`WillseyEtAl21`. An e-hypergraph over a
copy-discard category, e.g. :class:`discopy.markov.Diagram`, is a pair of a
:class:`discopy.hypergraph.Hypergraph` that is left-monogamous and acyclic,
i.e. a diagram with sharing whose every spider has one producer, a domain
position or the output of a box, its boxes the e-nodes, and of an
equivalence relation on its spiders of one type, its classes the e-classes.

Over cartesian diagrams an e-hypergraph is an e-graph: it hash-conses a
diagram as egg does a term, :meth:`EHypergraph.rebuild` closes the relation
under congruence and :meth:`EHypergraph.rewrite` glues the right-hand side of
an equation onto a region and relates their outputs. It denotes its
**sections**, each a choice of one producer for each class it needs, those of
the codomain and those read by the boxes it keeps: those it chooses and those
that are not affine. A section chooses per class where egg's terms choose per
occurrence, so that relating classes removes sections, but the classes are
egg's and :meth:`EHypergraph.extract` is a section of least tree cost.

The flags of a :class:`discopy.markov.Box` go beyond terms: equal boxes on
related inputs have related outputs only when deterministic, as two samples
are independent, and a box that is not affine, e.g. a condition, is an effect
every section keeps. Effects are context: equations are between cartesian
diagrams. Equality is up to renaming the spiders.

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
        ast_size
"""

from collections import Counter
from collections.abc import Callable
from math import inf
from typing import TYPE_CHECKING, Self

from networkx import DiGraph, NetworkXUnfeasible, topological_sort
from networkx.algorithms.isomorphism import is_isomorphic

from discopy import markov, messages
from discopy.abc import HypergraphCategory, MarkovCategory, MonoidalCategory
from discopy.axioms import (
    GENERATORS, Count, Equation, Hom, Obj, Serialisable, Var, axiom)
from discopy.drawing import Node
from discopy.hypergraph import Hypergraph, relabeling
from discopy.monoidal import Ty
from discopy.utils import (
    AxiomError,
    NamedGeneric,
    classproperty,
    factory_name,
    from_tree,
    pushout,
    resolve_factory,
    unbiased,
)

if TYPE_CHECKING:
    from hypothesis import strategies as st


def partition(n: int, pairs) -> tuple[int, ...]:
    """
    The finest partition of ``range(n)`` relating each pair, as the least
    element of the class of each element, so that it only depends on the
    partition.

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


def ast_size(_box) -> int:
    """ The cost of a box in egg's ``AstSize``: one, whatever the box. """
    return 1


class EHypergraph[category](
        MonoidalCategory["Ty", "EHypergraph"], NamedGeneric, Serialisable):
    """
    An e-hypergraph over a copy-discard ``category``, see
    :mod:`discopy.ehypergraph`.

    Parameters:
        graph : A left-monogamous acyclic hypergraph, whose boxes are the
            e-nodes.
        classes : The least spider related to each spider, the e-classes,
            the identity relation by default.

    Example
    -------
    >>> from discopy.markov import Ty, Box
    >>> x = Ty('x')
    >>> one, two = Box('1', Ty(), x), Box('2', Ty(), x)
    >>> times, shift = Box('*', x @ x, x), Box('<<', x @ x, x)
    >>> graph = EHypergraph[markov.Diagram].from_diagram(x @ two >> times)

    The equation ``a * 2 = a << 1`` rewrites the boxes 0 and 1 from the
    spider 0 of ``a`` to the spider 2 of ``a * 2``. Both sides cost three, a
    domain position and two boxes, and extraction takes the least producer of
    least cost, unless multiplication costs more than a shift:

    >>> left, right = x @ two >> times, x @ one >> shift
    >>> rewritten = graph.rewrite((0, 1), (0, ), (2, ), right.to_hypergraph())
    >>> assert rewritten.sections() == [
    ...     left.to_hypergraph(), right.to_hypergraph()]
    >>> assert rewritten.extract() == left.to_hypergraph()
    >>> cost = lambda box: 2 if box == times else 1
    >>> assert rewritten.extract(box_cost=cost) == right.to_hypergraph()
    """
    ob = classproperty(lambda cls: cls.category.ob)

    def __init__(
            self, graph: Hypergraph, classes: tuple[int, ...] | None = None):
        if not graph.is_left_monogamous or not graph.is_acyclic:
            raise AxiomError(messages.NOT_SHARING.format(graph))
        n = graph.n_spiders
        classes = tuple(range(n)) if classes is None else tuple(classes)
        if len(classes) != n:
            raise ValueError(messages.TYPE_ERROR.format(n, len(classes)))
        if any(graph.spider_types[s] != graph.spider_types[c]
               for s, c in enumerate(classes)):
            raise AxiomError(messages.TYPE_ERROR.format(
                "related spiders of one type", classes))
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
        >>> graph = EHypergraph[markov.Diagram].from_diagram(
        ...     two @ two >> divide)
        >>> graph.classes
        (0, 0, 2)
        """
        return cls(Hypergraph[cls.category].from_diagram(diagram)).rebuild()

    @classmethod
    def id(cls, dom=None) -> Self:
        return cls(Hypergraph[cls.category].id(dom))

    def carry(self, graph: Hypergraph, wires, spiders, pairs) -> Self:
        """
        The e-hypergraph of a hypergraph built from some wires and spiders,
        with pairs of them related, carried to the labels the hypergraph
        gives them, see :func:`hypergraph.relabeling`.
        """
        dom_wires, box_wires, cod_wires = wires
        label = relabeling(dom_wires + tuple(
            s for src, tgt in box_wires for s in src + tgt) + cod_wires,
            spiders)
        return type(self)(graph, partition(graph.n_spiders, (
            (label[s], label[t]) for s, t in pairs)))

    @unbiased
    def then(self, other: Self) -> Self:
        """
        Composition, that of the hypergraphs with both relations carried
        along the pushout.
        """
        left, right = pushout(
            self.graph.n_spiders, other.graph.n_spiders,
            self.graph.cod_wires, other.graph.dom_wires)
        (dom_wires, box_wires, _), (_, others, cod_wires) = relabel(
            self.graph.wires, left.get), relabel(other.graph.wires, right.get)
        pairs = [(left[s], left[c]) for s, c in enumerate(self.classes)] + [
            (right[s], right[c]) for s, c in enumerate(other.classes)]
        return self.carry(
            self.graph >> other.graph, (dom_wires, box_wires + others,
                                        cod_wires),
            set(left.values()) | set(right.values()), pairs)

    @unbiased
    def tensor(self, other: Self) -> Self:
        """ Tensor, the disjoint union of the hypergraphs and relations. """
        n = self.graph.n_spiders
        wires = tuple(map(lambda x, y: x + y, self.graph.wires, relabel(
            other.graph.wires, n.__add__)))
        pairs = list(enumerate(self.classes)) + [
            (n + s, n + c) for s, c in enumerate(other.classes)]
        return self.carry(
            self.graph @ other.graph, wires,
            range(n + other.graph.n_spiders), pairs)

    def merge(self, *spiders: int) -> Self:
        """ Relate spiders of one type, i.e. state that they are equal. """
        pairs = list(enumerate(self.classes)) + list(zip(spiders, spiders[1:]))
        return type(self)(self.graph, partition(self.graph.n_spiders, pairs))

    def pair(self, i: int, j: int) -> tuple[int, ...]:
        """
        Two spiders of one type, the ``i``-th modulo their number and the
        ``j``-th of its type, for the laws to quantify over: none when there
        is no spider.
        """
        if not self.graph.n_spiders:
            return ()
        types = self.graph.spider_types
        first = i % len(types)
        same = [s for s, typ in enumerate(types) if typ == types[first]]
        return first, same[j % len(same)]

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
        The congruence closure of the relation, egg's rebuild: the least
        relation containing it that relates the outputs of two equal boxes
        that are deterministic and read related inputs. Two samples on
        related inputs stay independent.
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
        Add a box reading some spiders, egg's add, and return the spiders of
        its outputs: an equal box reading the same classes is not added
        again, its outputs standing for those of the box.
        """
        key = tuple(self.classes[s] for s in inputs)
        for other, (src, tgt) in zip(self.graph.boxes, self.graph.box_wires):
            if other == box and tuple(self.classes[s] for s in src) == key:
                return self, tgt
        graph, n = self.graph, self.graph.n_spiders
        outputs = tuple(range(n, n + len(box.cod)))
        wires = (graph.dom_wires, graph.box_wires + (
            (tuple(inputs), outputs), ), graph.cod_wires)
        result = self.carry(
            type(graph)(graph.dom, graph.cod, graph.boxes + (box, ), wires),
            wires, range(n + len(outputs)), enumerate(self.classes))
        return result, result.graph.box_wires[-1][1]

    def assert_equation(self, region: tuple[int, ...], dom: tuple[int, ...],
                        cod: tuple[int, ...], rhs: Hypergraph):
        """ Raise unless :meth:`rewrite` can enter an equation, see there. """
        graph, classes = self.graph, self.classes
        for box in tuple(graph.boxes[j] for j in region) + rhs.boxes:
            if not box.is_cartesian:
                raise AxiomError(messages.NOT_CARTESIAN.format(box))
        if not rhs.is_left_monogamous or not rhs.is_acyclic:
            raise AxiomError(messages.NOT_SHARING.format(rhs))
        types = [graph.spider_types[s] for s in dom + cod]
        if (len(dom), len(cod)) != (len(rhs.dom), len(rhs.cod)) or types != [
                rhs.spider_types[s] for s in rhs.dom_wires + rhs.cod_wires]:
            raise AxiomError(messages.NOT_A_BOUNDARY.format(rhs, dom, cod))
        inside = {classes[s] for s in dom} | {
            classes[s] for j in region for s in graph.box_wires[j][1]}
        if any(classes[s] not in inside for s in cod + tuple(
                s for j in region for s in graph.box_wires[j][0])):
            raise AxiomError(messages.NOT_A_REGION.format(region, dom, cod))

    def rewrite(self, region: tuple[int, ...], dom: tuple[int, ...],
                cod: tuple[int, ...], rhs: Hypergraph) -> Self:
        """
        State that a region, the boxes computing the spiders ``cod`` from
        ``dom``, equals a hypergraph ``rhs``: glue it onto ``dom``,
        hash-consing its boxes with :meth:`add`, and relate ``cod`` to its
        outputs. The region stays: an e-graph never deletes, a section may.
        It raises :class:`AxiomError` when a box of either side is not
        cartesian, an effect being context, when the boundaries have other
        types, when the region does not compute ``cod`` from ``dom`` or when
        ``rhs`` is not a diagram with sharing.

        Rewriting a box into itself changes nothing:

        >>> from discopy.markov import Ty, Box
        >>> x = Ty('x')
        >>> f = Box('f', x, x)
        >>> graph = EHypergraph[markov.Diagram].from_diagram(f)
        >>> assert graph.rewrite((0, ), (0, ), (1, ), f.to_hypergraph())\\
        ...     == graph
        """
        dom, cod = tuple(dom), tuple(cod)
        self.assert_equation(region, dom, cod, rhs)
        result, image = self, dict(zip(rhs.dom_wires, dom))
        pending = list(range(len(rhs.boxes)))
        while pending:
            j = next(j for j in pending
                     if set(rhs.box_wires[j][0]) <= image.keys())
            pending.remove(j)
            result, outputs = result.add(
                rhs.boxes[j], tuple(image[s] for s in rhs.box_wires[j][0]))
            image.update(zip(rhs.box_wires[j][1], outputs))
        for spider, target in zip(cod, rhs.cod_wires):
            result = result.merge(spider, image[target])
        return result

    @property
    def producers(self) -> dict[int, tuple[int, ...]]:
        """
        The producers of each class, as ports of the hypergraph in order,
        the domain positions before the outputs of the boxes.
        """
        result: dict[int, list[int]] = {}
        for spider, (ports, _) in enumerate(self.graph.spider_wires):
            result.setdefault(self.classes[spider], []).extend(ports)
        return {q: tuple(sorted(ports)) for q, ports in result.items()}

    def roots(self) -> tuple[int, ...]:
        """
        The boxes every section keeps, those that are not affine, but for
        the later of two equal deterministic ones on related inputs: a hard
        constraint observed twice is observed once.
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
        The section of a choice of a producer port for each class it needs,
        see :meth:`needs`: the hypergraph of the roots and of the boxes it
        chooses, in a causal order, with a spider for each class it needs and
        a fresh one, discarded, for each producer it does not choose, which
        decodes to a diagram. It raises :class:`AxiomError` on a cycle.
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

        def consume(wires):
            return tuple(classes[s] for s in wires)

        wires = produce(graph.dom_wires), tuple(
            (consume(graph.box_wires[j][0]), produce(graph.box_wires[j][1]))
            for j in kept), consume(graph.cod_wires)
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
        The least tree cost of each class, a shared subterm counted once per
        occurrence, by Bellman-Ford relaxation to a fixpoint, and the least of
        its producers of least cost: exact, and the choice acyclic, when every
        box costs at least one. A box costs ``box_cost(box)``, one as in egg's
        ``AstSize`` by default, and a domain position ``input_cost``.
        """
        producers = self.producers
        costs = dict.fromkeys(producers, inf)

        def weight(port):
            box = self.box_of(port)
            return input_cost if box is None\
                else self.tree_cost(box, costs, box_cost)

        changed = True
        while changed:
            changed = False
            for q, ports in producers.items():
                least = min(map(weight, ports))
                if least < costs[q]:
                    costs[q], changed = least, True
        return costs, {q: next(p for p in ports if weight(p) == costs[q])
                       for q, ports in producers.items()}

    def cost(self, box_cost: Callable = ast_size, input_cost: float = 1
             ) -> float:
        """
        The least tree cost of a section: those of the classes of the
        codomain and of each root, see :meth:`relax`.
        """
        costs, _ = self.relax(box_cost, input_cost)
        return sum(costs[self.classes[s]] for s in self.graph.cod_wires) + sum(
            self.tree_cost(j, costs, box_cost) for j in self.roots())

    def extract(self, box_cost: Callable = ast_size, input_cost: float = 1
                ) -> Hypergraph:
        """
        A section of least tree cost, egg's extraction, see :meth:`relax`.
        """
        return self.section(self.relax(box_cost, input_cost)[1])

    def to_graph(self) -> DiGraph:
        """ The labelled graph of the hypergraph, with a node per class. """
        graph = self.graph.to_graph()
        for spider, label in enumerate(self.classes):
            obj = self.graph.spider_types[spider]
            graph.add_node(("class", label), box="class")
            graph.add_edge(
                ("class", label), Node("spider", i=spider, obj=obj))
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
        return {
            'factory': factory_name(EHypergraph),
            'category': factory_name(self.category),
            'graph': self.graph.to_tree(),
            'classes': list(self.classes)}

    @classmethod
    def from_tree(cls, tree: dict) -> Self:
        """ Decode a serialised e-hypergraph, see :meth:`to_tree`. """
        factory = cls[resolve_factory(tree['category'])]
        return factory(from_tree(tree['graph']), tuple(tree['classes']))

    @classmethod
    def strategy(cls, effects: bool = False, max_merges: int = 3, **params
                 ) -> "st.SearchStrategy[EHypergraph]":
        """
        Generate e-hypergraphs: an acyclic hypergraph of the category, its
        types and boxes named after two generators so that some are equal,
        then up to ``max_merges`` merges. The boxes are cartesian unless
        ``effects``, and ``params`` are passed to :meth:`Hypergraph.strategy`.
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

    # The laws: the hypergraph of an e-hypergraph is a strict monoidal functor.

    @axiom
    def graph_identity[X: Obj[Ty]](
            cls, x: Var[Ty, X]) -> Equation[Hypergraph]:
        """ The hypergraph of an identity is the identity hypergraph. """
        return Equation(cls.id(x).graph, Hypergraph[cls.category].id(x))

    @axiom
    def graph_composition[A: Obj[Ty], B: Obj[Ty], C: Obj[Ty]](
            cls, f: Hom[Self, A, B], g: Hom[Self, B, C]
    ) -> Equation[Hypergraph]:
        """ The hypergraph of a composite composes the hypergraphs. """
        return Equation((f >> g).graph, f.graph >> g.graph)

    @axiom
    def graph_tensor[A: Obj[Ty], B: Obj[Ty], C: Obj[Ty], D: Obj[Ty]](
            cls, f: Hom[Self, A, B], g: Hom[Self, C, D]
    ) -> Equation[Hypergraph]:
        """ The hypergraph of a tensor tensors the hypergraphs. """
        return Equation((f @ g).graph, f.graph @ g.graph)

    # Merging spiders states an equivalence relation.

    @axiom
    def merge_reflexivity[I: Count](
            cls, graph: Self, i: Var[int, I]) -> Equation[Self]:
        """ A spider is related to itself already. """
        return Equation(graph.merge(*graph.pair(i, i)[:1] * 2), graph)

    @axiom
    def merge_symmetry[I: Count, J: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J]
    ) -> Equation[Self]:
        """ Relating ``s`` to ``t`` relates ``t`` to ``s``. """
        pair = graph.pair(i, j)
        return Equation(graph.merge(*pair), graph.merge(*pair[::-1]))

    @axiom
    def merge_transitivity[I: Count, J: Count, K: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J],
            k: Var[int, K]) -> Equation[Self]:
        """ Relating ``s`` to ``t`` and ``t`` to ``u`` relates them all. """
        if not graph.graph.n_spiders:
            return Equation(graph, graph)
        (s, t), (_, u) = graph.pair(i, j), graph.pair(i, k)
        chained = graph.merge(s, t).merge(t, u)
        return Equation(chained.merge(s, u), chained)

    # Congruence closure: the least congruence containing the relation.

    @axiom
    def rebuild_idempotence(cls, graph: Self) -> Equation[Self]:
        """ A congruence is its own closure. """
        closed = graph.rebuild()
        return Equation(closed.rebuild(), closed)

    @axiom
    def rebuild_extensivity[I: Count, J: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J]
    ) -> Equation[Self]:
        """ Closing a relation keeps the equations it had. """
        merged = graph.merge(*graph.pair(i, j))
        return Equation(merged.rebuild().merge(*graph.pair(i, j)),
                        merged.rebuild())

    @axiom
    def rebuild_confluence[I: Count, J: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J]
    ) -> Equation[Self]:
        """ Closing before an equation or only after gives one congruence. """
        pair = graph.pair(i, j)
        return Equation(graph.merge(*pair).rebuild(),
                        graph.rebuild().merge(*pair).rebuild())

    @axiom
    def congruence[A: Obj[Ty], B: Obj[Ty]](
            cls, f: Hom[Self, A, B]) -> Equation[tuple[bool, ...]]:
        """
        Relating the inputs of two copies of a hypergraph relates two of
        their outputs exactly when every box they depend on is deterministic:
        equal boxes on related inputs have related outputs when they are
        deterministic, while two samples are independent.
        """
        graph, n, m = f.graph, len(f.dom), len(f.cod)
        twice = type(f)(graph @ graph)
        for k in range(n):
            twice = twice.merge(
                twice.graph.dom_wires[k], twice.graph.dom_wires[n + k])
        cod, classes = twice.graph.cod_wires, twice.rebuild().classes

        def determined(spider):
            box = f.box_of(min(graph.spider_wires[spider][0]))
            return box is None or graph.boxes[box].is_deterministic and all(
                map(determined, graph.box_wires[box][0]))

        return Equation(
            tuple(classes[cod[k]] == classes[cod[m + k]] for k in range(m)),
            tuple(map(determined, graph.cod_wires)))

    # Sections and extraction: a section of least tree cost.

    @axiom
    def extraction_soundness(cls, graph: Self) -> Equation[bool]:
        """ What is extracted is one of the sections. """
        return Equation(graph.extract() in graph.sections(), True)

    @axiom
    def extraction_validity(cls, graph: Self) -> Equation[Hypergraph]:
        """ What is extracted decodes to a diagram that encodes back to it. """
        extracted = graph.extract()
        return Equation(extracted.to_diagram().to_hypergraph(), extracted)

    @axiom
    def extraction_optimality(cls, graph: Self) -> Equation[int]:
        """ No section costs less than what is extracted. """
        return Equation(graph.cost(), min(
            type(graph)(section).cost() for section in graph.sections()))

    @axiom
    def extraction_idempotence(cls, graph: Self) -> Equation[Hypergraph]:
        """ What is extracted is all its own e-hypergraph extracts. """
        extracted = graph.extract()
        return Equation(type(graph)(extracted).extract(), extracted)

    @axiom
    def effects_kept(cls, graph: Self) -> Equation[bool]:
        """
        Every section keeps every box that is not affine, all of those that
        are not deterministic either, and one of equal deterministic ones.
        """
        effects = [box for box in graph.graph.boxes if not box.is_affine]
        samples = Counter(box for box in effects if not box.is_deterministic)
        return Equation(all(
            set(effects) <= set(section.boxes)
            and samples <= Counter(section.boxes)
            for section in graph.sections()), True)

    # Rewriting: an equation glued onto a region.

    @axiom
    def rewrite_identity(cls, graph: Self) -> Equation[Self]:
        """
        Rewriting a rebuilt e-hypergraph into its own hypergraph, glued onto
        the least spider of each class of its domain, changes nothing: each
        of its boxes is hash-consed into itself, modulo the relation.
        """
        rebuilt, (dom_wires, _, cod_wires) = graph.rebuild(), graph.graph.wires
        return Equation(rebuilt.rewrite(
            tuple(range(len(graph.graph.boxes))),
            tuple(rebuilt.classes[s] for s in dom_wires), cod_wires,
            graph.graph), rebuilt)

    @axiom
    def extraction_rewrite[A: Obj[Ty], B: Obj[Ty]](
            cls, f: Hom[Self, A, B], g: Hom[Self, A, B]) -> Equation[bool]:
        """
        Rewriting the whole of ``f`` into what ``g`` extracts costs no more
        than either: a rewrite adds producers and relates classes, which
        lowers the least cost of each.
        """
        rewritten = f.rewrite(
            tuple(range(len(f.graph.boxes))), f.graph.dom_wires,
            f.graph.cod_wires, g.extract())
        return Equation(rewritten.cost() <= min(f.cost(), g.cost()), True)

    rebuild_idempotence = rebuild_idempotence.weaken(effects=True)
    rebuild_extensivity = rebuild_extensivity.weaken(effects=True)
    rebuild_confluence = rebuild_confluence.weaken(effects=True)
    congruence = congruence.weaken(effects=True)
    extraction_soundness = extraction_soundness.weaken(effects=True)
    extraction_validity = extraction_validity.weaken(effects=True)
    extraction_optimality = extraction_optimality.weaken(effects=True)
    extraction_idempotence = extraction_idempotence.weaken(effects=True)
    effects_kept = effects_kept.weaken(effects=True)


Markov = EHypergraph[markov.Diagram]
