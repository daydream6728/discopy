# -*- coding: utf-8 -*-

"""
E-hypergraphs, i.e. hypergraphs with an equivalence relation on their spiders.

An e-hypergraph over a category ``C`` is a triple ``(graph, ~, alternatives)``
of

* a :class:`discopy.hypergraph.Hypergraph` ``graph`` over ``C``,
* an equivalence relation ``~`` on the spiders of ``graph``, relating only
  spiders of the same type, and
* a list of alternatives, i.e. pairs of sets of boxes of ``graph`` that may
  replace one another.

The structure of ``C`` is wiring already, a snake in a compact category, a
fused spider in a hypergraph one, a swap or a copy, so the relation and the
alternatives are all an e-hypergraph adds to a hypergraph. The relation is
kept apart from the wiring: in ``graph`` a spider with two producers is the
Frobenius merge of both, while ``s ~ t`` says that ``s`` and ``t`` carry the
same value in any section.

An equation enters through :meth:`EHypergraph.rewrite`, which states that a
region of ``graph``, i.e. a set of its boxes, equals a hypergraph ``rhs``
with the same boundary: it adds ``rhs``, relates its domain and codomain to
the boundary of the region and records the region and ``rhs`` as
alternatives. Relating two wires of an existing diagram makes no sense over a
symmetric category, where a wire has one consumer: what makes sense is that
one subdiagram may replace another.

An e-hypergraph denotes the set of its **sections**: one for each choice of
a side of every alternative, keeping every box but those on the sides not
chosen, with the spiders of each class of ``~`` identified. The sections that
are hypergraphs of ``C`` are those that decode to a diagram, and
:meth:`EHypergraph.extract` is one of least :meth:`EHypergraph.cost`.

* :meth:`EHypergraph.rebuild` closes ``~`` under congruence: two boxes with
  the same label on related inputs have related outputs, and are recorded as
  alternatives. A Markov category is the one exception, as its boxes need not
  be deterministic, e.g. two samples of a distribution on the same input
  need not be equal.
* :meth:`EHypergraph.then` and :meth:`EHypergraph.tensor` are those of the
  hypergraphs, the relation carried along the pushout, so that e-hypergraphs
  over ``C`` form a monoidal category of their own.

Equality is up to renaming the spiders, as for hypergraphs. The laws of
e-hypergraphs are stated on :class:`EHypergraph` and checked by the property
matrix on every alias of this module.

Note
----
:meth:`EHypergraph.rebuild` is a least fixpoint, which relates nothing on a
feedback loop: two copies of a cycle are related only coinductively, as a
greatest fixpoint, i.e. a bisimulation, would relate them.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    EHypergraph
"""

from itertools import product
from typing import Self

from networkx import Graph
from networkx.algorithms.isomorphism import is_isomorphic

from discopy import compact, frobenius, markov, messages, symmetric
from discopy.abc import MarkovCategory, MonoidalCategory
from discopy.axioms import (
    Count, Equation, Hom, Obj, Serialisable, Var, axiom)
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


class EHypergraph[category](
        MonoidalCategory["Ty", "EHypergraph"], NamedGeneric, Serialisable):
    """
    An e-hypergraph over a ``category``: a hypergraph with an equivalence
    relation on its spiders and alternatives between its boxes, see
    :mod:`discopy.ehypergraph`.

    Parameters:
        graph : The hypergraph.
        classes : The least spider related to each spider, the identity
            relation by default.
        alternatives : Pairs of tuples of boxes that may replace one another.

    Example
    -------
    >>> from discopy.symmetric import Ty, Box
    >>> x = Ty('x')
    >>> f, g, h = Box('f', x, x), Box('g', x, x), Box('h', x, x)
    >>> E = EHypergraph[symmetric.Diagram]
    >>> graph = E.from_diagram(f >> g >> h)

    Rewriting ``f >> g``, the boxes 0 and 1 between the spiders 0 and 2, into
    ``h`` adds ``h`` as an alternative, which extraction takes:

    >>> rhs = h.to_hypergraph()
    >>> rewritten = graph.rewrite((0, 1), (0, ), (2, ), rhs)
    >>> len(rewritten.sections())
    2
    >>> print(rewritten.extract().to_diagram())
    h >> h
    """
    ob = classproperty(lambda cls: cls.category.ob)

    def __init__(
            self, graph: Hypergraph, classes: tuple[int, ...] | None = None,
            alternatives: tuple[tuple[tuple[int, ...], ...], ...] = ()):
        self.graph = graph
        n = graph.n_spiders
        classes = tuple(range(n)) if classes is None else tuple(classes)
        if len(classes) != n:
            raise ValueError(messages.TYPE_ERROR.format(n, len(classes)))
        if any(graph.spider_types[s] != graph.spider_types[c]
               for s, c in enumerate(classes)):
            raise AxiomError(messages.TYPE_ERROR.format(
                "related spiders of one type", classes))
        self.classes = partition(n, enumerate(classes))
        self.alternatives = tuple(
            (tuple(left), tuple(right)) for left, right in alternatives)

    @property
    def dom(self):
        """ The domain of the e-hypergraph, that of its hypergraph. """
        return self.graph.dom

    @property
    def cod(self):
        """ The codomain of the e-hypergraph, that of its hypergraph. """
        return self.graph.cod

    @classmethod
    def from_diagram(cls, diagram) -> Self:
        """ The e-hypergraph of a diagram, with the identity relation. """
        return cls(Hypergraph[cls.category].from_diagram(diagram))

    @classmethod
    def id(cls, dom=None) -> Self:
        return cls(Hypergraph[cls.category].id(dom))

    @classmethod
    def swap(cls, left, right) -> Self:
        """ The swap of the category, i.e. wiring. """
        return cls(Hypergraph[cls.category].swap(left, right))

    def carry(self, graph: Hypergraph, wires, spiders, pairs,
              alternatives) -> Self:
        """
        The e-hypergraph of a hypergraph built from wires, with the spiders
        related by pairs of the same labels as these wires, carried to the
        labels the hypergraph gives them, see :func:`hypergraph.relabeling`.

        Parameters:
            graph : The hypergraph built from the wires.
            wires : Its wires, before the hypergraph relabels its spiders.
            spiders : Every spider, labelled as in the wires.
            pairs : The pairs of related spiders, labelled as in the wires.
            alternatives : The alternatives, between boxes of the graph.
        """
        dom_wires, box_wires, cod_wires = wires
        flat = dom_wires + tuple(
            s for src, tgt in box_wires for s in src + tgt) + cod_wires
        label = relabeling(flat, spiders)
        return type(self)(graph, partition(graph.n_spiders, (
            (label[s], label[t]) for s, t in pairs)), alternatives)

    @unbiased
    def then(self, other: Self) -> Self:
        """
        Composition, that of the hypergraphs with both relations carried
        along the pushout and the alternatives of both.
        """
        left, right = pushout(
            self.graph.n_spiders, other.graph.n_spiders,
            self.graph.cod_wires, other.graph.dom_wires)
        wires = (
            tuple(left[s] for s in self.graph.dom_wires),
            tuple((tuple(left[s] for s in src), tuple(left[s] for s in tgt))
                  for src, tgt in self.graph.box_wires) + tuple(
                (tuple(right[s] for s in src), tuple(right[s] for s in tgt))
                for src, tgt in other.graph.box_wires),
            tuple(right[s] for s in other.graph.cod_wires))
        pairs = [(left[s], left[c]) for s, c in enumerate(self.classes)]
        pairs += [(right[s], right[c]) for s, c in enumerate(other.classes)]
        return self.carry(
            self.graph >> other.graph, wires,
            set(left.values()) | set(right.values()), pairs,
            self.alternatives + other.shift(len(self.graph.boxes)))

    @unbiased
    def tensor(self, other: Self) -> Self:
        """ Tensor, the disjoint union of the hypergraphs and relations. """
        n = self.graph.n_spiders
        shift = lambda wires: tuple(n + s for s in wires)
        wires = (
            self.graph.dom_wires + shift(other.graph.dom_wires),
            self.graph.box_wires + tuple(
                (shift(src), shift(tgt))
                for src, tgt in other.graph.box_wires),
            self.graph.cod_wires + shift(other.graph.cod_wires))
        pairs = list(enumerate(self.classes)) + [
            (n + s, n + c) for s, c in enumerate(other.classes)]
        return self.carry(
            self.graph @ other.graph, wires,
            range(n + other.graph.n_spiders), pairs,
            self.alternatives + other.shift(len(self.graph.boxes)))

    def dagger(self) -> Self:
        """ The dagger, that of the hypergraph with the same relation. """
        dom_wires, box_wires, cod_wires = self.graph.wires
        wires = cod_wires, tuple(
            (tgt, src) for src, tgt in box_wires[::-1]), dom_wires
        last = len(self.graph.boxes) - 1
        flip = lambda boxes: tuple(last - i for i in boxes)
        return self.carry(
            self.graph.dagger(), wires, range(self.graph.n_spiders),
            list(enumerate(self.classes)), tuple(
                (flip(left), flip(right))
                for left, right in self.alternatives))

    def shift(self, offset: int) -> tuple:
        """
        The alternatives with every box shifted by an offset, e.g. to make
        room for the boxes of another e-hypergraph.

        Parameters:
            offset : The number to add to each box.
        """
        return tuple(
            (tuple(offset + i for i in left), tuple(offset + i for i in right))
            for left, right in self.alternatives)

    def rewrite(self, region: tuple[int, ...], dom: tuple[int, ...],
                cod: tuple[int, ...], rhs: Hypergraph) -> Self:
        """
        State that a region equals a hypergraph with the same boundary: add
        ``rhs``, relate its domain to ``dom`` and its codomain to ``cod``, and
        record the region and ``rhs`` as alternatives.

        Parameters:
            region : The boxes of the left-hand side.
            dom : The spiders the region reads, in the order of ``rhs.dom``.
            cod : The spiders the region writes, in the order of ``rhs.cod``.
            rhs : The right-hand side.
        """
        n, m = self.graph.n_spiders, len(self.graph.boxes)
        shift = lambda wires: tuple(n + s for s in wires)
        dom_wires, box_wires, cod_wires = self.graph.wires
        wires = dom_wires, box_wires + tuple(
            (shift(src), shift(tgt)) for src, tgt in rhs.box_wires), cod_wires
        types = dict(enumerate(self.graph.spider_types))
        types.update({n + s: t for s, t in enumerate(rhs.spider_types)})
        graph = type(self.graph)(
            self.dom, self.cod, self.graph.boxes + rhs.boxes, wires, types)
        pairs = list(enumerate(self.classes))
        pairs += zip(shift(rhs.dom_wires), dom)
        pairs += zip(shift(rhs.cod_wires), cod)
        return self.carry(
            graph, wires, range(n + rhs.n_spiders), pairs,
            self.alternatives + ((
                tuple(region), tuple(range(m, m + len(rhs.boxes)))), ))

    def merge(self, *spiders: int) -> Self:
        """
        Relate spiders of one type, i.e. assert an equation between them.

        Parameters:
            spiders : The spiders to relate, any number of them.
        """
        pairs = list(enumerate(self.classes)) + list(zip(spiders, spiders[1:]))
        return type(self)(self.graph, partition(
            self.graph.n_spiders, pairs), self.alternatives)

    def pair(self, i: int, j: int) -> tuple[int, ...]:
        """
        Two spiders of one type, chosen by two numbers, for the laws to
        quantify over: none when there is no spider at all.

        Parameters:
            i : Chooses the first spider, modulo their number.
            j : Chooses the second among those of the same type.
        """
        if not self.graph.n_spiders:
            return ()
        types = self.graph.spider_types
        first = i % len(types)
        same = [s for s, typ in enumerate(types) if typ == types[first]]
        return first, same[j % len(same)]

    is_deterministic = classproperty(
        lambda cls: not issubclass(cls.category, MarkovCategory))
    """
    Whether two boxes with the same label on related inputs have related
    outputs, i.e. whether :meth:`rebuild` closes under congruence: all but in
    a Markov category.
    """

    def rebuild(self) -> Self:
        """
        The least congruence containing the relation, the later of two
        congruent boxes recorded as an alternative to the first.
        """
        if not self.is_deterministic:
            return self
        graph, result = self.graph, self
        known = {frozenset(pair) for pair in self.alternatives}
        while True:
            first, pairs, alternatives = {}, [], list(result.alternatives)
            for i, (box, (src, tgt)) in enumerate(
                    zip(graph.boxes, graph.box_wires)):
                key = box, tuple(result.classes[s] for s in src)
                j = first.setdefault(key, i)
                pairs += zip(graph.box_wires[j][1], tgt)
                if j != i and frozenset([(i, ), (j, )]) not in known:
                    known.add(frozenset([(i, ), (j, )]))
                    alternatives.append(((i, ), (j, )))
            merged = type(self)(graph, result.classes, tuple(alternatives))
            for s, t in pairs:
                merged = merged.merge(s, t)
            if merged.classes == result.classes\
                    and merged.alternatives == result.alternatives:
                return result
            result = merged

    def section(self, kept: tuple[int, ...]) -> Hypergraph:
        """
        The hypergraph of some boxes, with the spiders of each class of the
        relation identified.

        Parameters:
            kept : The boxes to keep.
        """
        graph = self.graph
        dom_wires, box_wires, cod_wires = graph.wires
        ported = {s for wires in box_wires for side in wires for s in side}
        loose = [s for s in range(graph.n_spiders) if s not in ported
                 and s not in dom_wires and s not in cod_wires]
        used = list(dict.fromkeys(self.classes[s] for s in (
            dom_wires + tuple(s for i in kept for side in box_wires[i]
                              for s in side) + cod_wires + tuple(loose))))
        kept = self.causal_order(kept)
        label = {c: k for k, c in enumerate(used)}
        relabel = lambda wires: tuple(label[self.classes[s]] for s in wires)
        return type(graph)(
            graph.dom, graph.cod, tuple(graph.boxes[i] for i in kept),
            (relabel(dom_wires), tuple(
                (relabel(box_wires[i][0]), relabel(box_wires[i][1]))
                for i in kept), relabel(cod_wires)),
            tuple(graph.spider_types[c] for c in used))

    def causal_order(self, boxes: tuple[int, ...]) -> tuple[int, ...]:
        """
        Some boxes, each after the boxes producing what it reads, as far as
        a cycle allows, and otherwise in their order.

        Parameters:
            boxes : The boxes to order.
        """
        box_wires, classes = self.graph.box_wires, self.classes
        producers = {classes[s]: i for i in boxes for s in box_wires[i][1]}
        result, pending = [], list(boxes)
        while pending:
            ready = [i for i in pending if all(
                producers.get(classes[s], i) in result + [i]
                for s in box_wires[i][0])]
            result += ready or pending[:1]
            pending = [i for i in pending if i not in result]
        return tuple(result)

    def sections(self) -> list[Hypergraph]:
        """
        Every section, i.e. one for each choice of a side of every
        alternative, hypergraph of the category or not.
        """
        result = []
        for choice in product(*self.alternatives):
            dropped = {i for (left, right), chosen in zip(
                self.alternatives, choice)
                for i in (right if chosen is left else left)}
            result.append(self.section(tuple(
                i for i in range(len(self.graph.boxes)) if i not in dropped)))
        return result

    @staticmethod
    def is_valid(graph: Hypergraph) -> bool:
        """ Whether a hypergraph decodes to a diagram of its category. """
        try:
            graph.to_diagram()
        except (AxiomError, NotImplementedError, ValueError):
            return False
        return True

    def represents(self, graph: Hypergraph) -> bool:
        """
        Whether a hypergraph is one of the sections of the e-hypergraph.

        Parameters:
            graph : The hypergraph.
        """
        return any(graph == section for section in self.sections())

    @staticmethod
    def cost(graph: Hypergraph) -> int:
        """ The cost of a hypergraph, its number of boxes. """
        return len(graph.boxes)

    def extract(self) -> Hypergraph:
        """
        A section of least cost that is a hypergraph of the category, the
        first in the order of :meth:`sections` among those of equal cost.
        """
        valid = [s for s in self.sections() if self.is_valid(s)]
        if not valid:
            raise AxiomError(messages.NO_SECTION.format(self))
        return min(valid, key=self.cost)

    def to_graph(self) -> Graph:
        """
        The labelled graph of the hypergraph, with a node per class and two
        per alternative, one for each side.
        """
        graph = self.graph.to_graph()
        for spider, label in enumerate(self.classes):
            obj = self.graph.spider_types[spider]
            graph.add_node(("class", label), box="class")
            graph.add_edge(
                ("class", label), Node("spider", i=spider, obj=obj))
        for k, sides in enumerate(self.alternatives):
            graph.add_edge(("side", k, 0), ("side", k, 1))
            for side, boxes in enumerate(sides):
                graph.add_node(("side", k, side), box="side")
                for i in boxes:
                    graph.add_edge(("side", k, side), Node(
                        "box", box=self.graph.boxes[i], i=i))
        return graph

    def __eq__(self, other) -> bool:
        if not isinstance(other, EHypergraph):
            return False
        if self.graph != other.graph:
            return False
        return is_isomorphic(
            self.to_graph(), other.to_graph(), lambda x, y: x == y)

    def __hash__(self) -> int:
        return hash((self.graph, len(self.alternatives), tuple(sorted(
            self.classes.count(c) for c in set(self.classes)))))

    def __repr__(self) -> str:
        return factory_name(type(self))\
            + f"(graph={self.graph!r}, classes={self.classes!r}, "\
            f"alternatives={self.alternatives!r})"

    def to_tree(self) -> dict:
        """ Serialise the e-hypergraph, with the name of its category. """
        return {
            'factory': factory_name(EHypergraph),
            'category': factory_name(self.category),
            'graph': self.graph.to_tree(),
            'classes': list(self.classes),
            'alternatives': [list(map(list, pair))
                             for pair in self.alternatives]}

    @classmethod
    def from_tree(cls, tree: dict) -> Self:
        """ Decode a serialised e-hypergraph, see :meth:`to_tree`. """
        factory = cls[resolve_factory(tree['category'])]
        return factory(
            from_tree(tree['graph']), tuple(tree['classes']),
            tree.get('alternatives', ()))

    @classmethod
    def strategy(cls, max_rewrites: int = 2, **params):
        """
        Generate e-hypergraphs: a hypergraph of the category, then up to
        ``max_rewrites`` rewrites of one of its boxes into a hypergraph with
        the same boundary.

        Parameters:
            max_rewrites : The largest number of rewrites.
            params : Passed to :meth:`Hypergraph.strategy`.
        """
        from hypothesis import strategies as st

        if cls.category is None:
            raise NotImplementedError(
                f"No strategy implemented for {factory_name(cls)}.")
        hypergraphs = Hypergraph[cls.category].strategy

        @st.composite
        def ehypergraphs(draw):
            graph = cls(draw(hypergraphs(**params)))
            for _ in range(draw(st.integers(0, max_rewrites))):
                if not graph.graph.boxes:
                    break
                i = draw(st.integers(0, len(graph.graph.boxes) - 1))
                box = graph.graph.boxes[i]
                src, tgt = graph.graph.box_wires[i]
                rhs = draw(hypergraphs(dom=box.dom, cod=box.cod, max_leaves=2))
                graph = graph.rewrite((i, ), src, tgt, rhs)
            return graph

        return ehypergraphs()

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

    # The laws of an equivalence relation, as a semilattice of equations.

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
    def merge_idempotence[I: Count, J: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J]
    ) -> Equation[Self]:
        """ An equation stated twice is stated once. """
        once = graph.merge(*graph.pair(i, j))
        return Equation(once.merge(*graph.pair(i, j)), once)

    @axiom
    def merge_commutativity[I: Count, J: Count, K: Count, L: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J],
            k: Var[int, K], l: Var[int, L]) -> Equation[Self]:
        """ Equations can be stated in any order. """
        first, second = graph.pair(i, j), graph.pair(k, l)
        return Equation(graph.merge(*first).merge(*second),
                        graph.merge(*second).merge(*first))

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
            cls, f: Hom[Self, A, B]) -> Equation[Self]:
        """
        A morphism applied twice to related inputs gives related outputs:
        relating the inputs of ``f @ f`` pairwise relates their outputs.
        """
        twice, n, m = f @ f, len(f.dom), len(f.cod)
        dom, cod = twice.graph.dom_wires, twice.graph.cod_wires
        inputs = twice
        for k in range(n):
            inputs = inputs.merge(dom[k], dom[n + k])
        closed = inputs.rebuild()
        outputs = closed
        for k in range(m):
            outputs = outputs.merge(cod[k], cod[m + k])
        return Equation(outputs, closed)

    # Extraction: one section of least cost among those of the category.

    @axiom
    def extraction_soundness(cls, graph: Self) -> Equation[bool]:
        """ What is extracted is one of the sections. """
        return Equation(graph.represents(graph.extract()), True)

    @axiom
    def extraction_validity(cls, graph: Self) -> Equation[Hypergraph]:
        """ What is extracted decodes to a diagram that encodes back to it. """
        extracted = graph.extract()
        return Equation(extracted.to_diagram().to_hypergraph(), extracted)

    @axiom
    def extraction_optimality(cls, graph: Self) -> Equation[int]:
        """ No section of the category costs less than what is extracted. """
        return Equation(cls.cost(graph.extract()), min(
            cls.cost(s) for s in graph.sections() if cls.is_valid(s)))

    @axiom
    def extraction_rewrite[A: Obj[Ty], B: Obj[Ty]](
            cls, f: Hom[Self, A, B], g: Hom[Self, A, B]) -> Equation[int]:
        """
        Rewriting the whole of ``f`` into the hypergraph of ``g`` costs the
        cheaper of the two: a rewrite only adds sections.
        """
        whole = tuple(range(len(f.graph.boxes)))
        rewritten = f.rewrite(
            whole, f.graph.dom_wires, f.graph.cod_wires, g.extract())
        return Equation(cls.cost(rewritten.extract()), min(
            cls.cost(f.extract()), cls.cost(g.extract())))

    @axiom
    def extraction_discreteness[A: Obj[Ty], B: Obj[Ty]](
            cls, f: Hom[Self, A, B]) -> Equation[Hypergraph]:
        """
        With no alternative nor relation, extraction is the identity: on the
        hypergraph extracted from ``f``, which is one of the category.
        """
        extracted = f.extract()
        return Equation(type(f)(extracted).extract(), extracted)


Symmetric = EHypergraph[symmetric.Diagram]
Compact = EHypergraph[compact.Diagram]
Markov = EHypergraph[markov.Diagram]
Frobenius = EHypergraph[frobenius.Diagram]

for markovian in (Markov, Frobenius):
    markovian.congruence = EHypergraph.congruence.inapplicable(
        messages.NOT_DETERMINISTIC)

for linear in (Symmetric, Compact):
    linear.congruence = EHypergraph.congruence.failing(
        messages.INDUCTIVE_CONGRUENCE)
Symmetric.congruence_acyclic = EHypergraph.congruence.weaken(acyclic=True)
