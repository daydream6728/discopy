# -*- coding: utf-8 -*-

"""
E-hypergraphs, i.e. hypergraphs with an equivalence relation on their spiders.

An e-hypergraph over a category ``C`` is a pair ``(graph, ~)`` of

* a :class:`discopy.hypergraph.Hypergraph` ``graph`` over ``C``, and
* an equivalence relation ``~`` on the spiders of ``graph``, relating only
  spiders of the same type,

where ``s ~ t`` says that the spiders ``s`` and ``t`` are alternatives: what
reads one may read the other instead. This is not the Frobenius merge of
``graph`` itself, where a spider with two producers is one wire carrying both:
the relation is kept apart from the wiring. The structure of ``C`` is wiring
already, a snake in a compact category, a fused spider in a hypergraph one,
a swap or a copy, so the relation is all an e-hypergraph adds to a
hypergraph.

An e-hypergraph denotes the set of its **sections**. A section chooses one
spider ``r(c)`` in each class ``c`` of ``~``, moves every port reading a
spider of ``c``, i.e. a box input or the codomain, onto ``r(c)``, and keeps
the boxes the codomain and the effects still depend on, or all of them in a
category that cannot discard. The sections that
are hypergraphs of ``C`` are those that decode to a diagram, e.g. acyclic
where ``C`` is not traced, and :meth:`EHypergraph.extract` is one of least
:meth:`EHypergraph.cost`.

Three operations act on the relation:

* :meth:`EHypergraph.merge` adds an equation, i.e. relates spiders,
* :meth:`EHypergraph.rebuild` closes ``~`` under congruence: two boxes with
  the same label on related inputs have related outputs. A Markov category
  is the one exception, as its boxes need not be deterministic, e.g. two
  samples of a distribution on the same input need not be equal.
* :meth:`EHypergraph.then` and :meth:`EHypergraph.tensor` are those of the
  hypergraphs, the relation carried along the pushout, so that e-hypergraphs
  over ``C`` form a monoidal category of their own.

Equality is up to renaming the spiders, as for hypergraphs. The laws of
e-hypergraphs are stated on :class:`EHypergraph` and checked by the property
matrix on every alias of this module.

Note
----
Where the boxes of ``C`` are linear, i.e. ``C`` is symmetric but not Markov,
what ``s ~ t`` asserts is an open question: a spider of a symmetric
hypergraph has one producer and one consumer, so it carries no value two
consumers could share, and congruence is sound only once we say what
replacing one spider by the other means. This module takes the reading above,
as sections, and closes under congruence everywhere but in a Markov
category. Its closure is a least fixpoint, which relates nothing on a
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
    relation on its spiders, see :mod:`discopy.ehypergraph`.

    Parameters:
        graph : The hypergraph.
        classes : The least spider related to each spider, the identity
            relation by default.

    Example
    -------
    >>> from discopy.markov import Ty, Box, Swap
    >>> x = Ty('x')
    >>> a, b, g = [Box(name, x, x) for name in "abg"]
    >>> h = Box('h', x @ x, x)
    >>> E = EHypergraph[markov.Diagram]
    >>> graph = E((a @ b >> Swap(x, x) >> g @ g >> h).to_hypergraph())

    Asserting ``a(x0) = b(x1)`` relates their outputs. The boxes of a Markov
    category need not be deterministic, so the two ``g`` reading them are two
    samples and :meth:`rebuild` relates nothing more:

    >>> merged = graph.merge(2, 3)
    >>> assert merged.rebuild() == merged

    Extraction then reads both ``g`` from ``a``, the cheapest alternative:

    >>> print(merged.extract().to_diagram())
    x @ Copy(x, 0) >> a >> Copy(x) >> g @ g >> h
    """
    ob = classproperty(lambda cls: cls.category.ob)

    def __init__(
            self, graph: Hypergraph, classes: tuple[int, ...] | None = None):
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

    def carry(self, graph: Hypergraph, wires, pairs) -> Self:
        """
        The e-hypergraph of a hypergraph built from wires, with the spiders
        related by pairs of the same labels as these wires, carried to the
        labels the hypergraph gives them, see :func:`hypergraph.relabeling`.

        Parameters:
            graph : The hypergraph built from the wires.
            wires : Its wires, before the hypergraph relabels its spiders.
            pairs : The pairs of related spiders, labelled as in the wires.
        """
        dom_wires, box_wires, cod_wires = wires
        flat = dom_wires + tuple(
            s for src, tgt in box_wires for s in src + tgt) + cod_wires
        spiders = {s for pair in pairs for s in pair}
        label = relabeling(flat, spiders)
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
        wires = (
            tuple(left[s] for s in self.graph.dom_wires),
            tuple((tuple(left[s] for s in src), tuple(left[s] for s in tgt))
                  for src, tgt in self.graph.box_wires) + tuple(
                (tuple(right[s] for s in src), tuple(right[s] for s in tgt))
                for src, tgt in other.graph.box_wires),
            tuple(right[s] for s in other.graph.cod_wires))
        pairs = [(left[s], left[c]) for s, c in enumerate(self.classes)]
        pairs += [(right[s], right[c]) for s, c in enumerate(other.classes)]
        return self.carry(self.graph >> other.graph, wires, pairs)

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
        return self.carry(self.graph @ other.graph, wires, pairs)

    def dagger(self) -> Self:
        """ The dagger, that of the hypergraph with the same relation. """
        dom_wires, box_wires, cod_wires = self.graph.wires
        wires = cod_wires, tuple(
            (tgt, src) for src, tgt in box_wires[::-1]), dom_wires
        return self.carry(
            self.graph.dagger(), wires, list(enumerate(self.classes)))

    def merge(self, *spiders: int) -> Self:
        """
        Relate spiders of one type, i.e. assert an equation between them.

        Parameters:
            spiders : The spiders to relate, any number of them.
        """
        pairs = list(enumerate(self.classes)) + list(zip(spiders, spiders[1:]))
        return type(self)(self.graph, partition(self.graph.n_spiders, pairs))

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

    can_discard = classproperty(
        lambda cls: issubclass(cls.category, MarkovCategory))
    """
    Whether a section may drop the boxes nothing reads, i.e. whether the
    category discards: a Markov category does, a linear one keeps them all.
    """

    is_deterministic = classproperty(
        lambda cls: not issubclass(cls.category, MarkovCategory))
    """
    Whether two boxes with the same label on related inputs have related
    outputs, i.e. whether :meth:`rebuild` closes under congruence: all but in
    a Markov category.
    """

    def rebuild(self) -> Self:
        """ The least congruence containing the relation, see the module. """
        if not self.is_deterministic:
            return self
        graph, result = self.graph, self
        while True:
            first, pairs = {}, []
            for box, (src, tgt) in zip(graph.boxes, graph.box_wires):
                key = box, tuple(result.classes[s] for s in src)
                pairs += zip(first.setdefault(key, tgt), tgt)
            merged = result
            for s, t in pairs:
                merged = merged.merge(s, t)
            if merged.classes == result.classes:
                return result
            result = merged

    def section(self, choice: dict[int, int]) -> Hypergraph:
        """
        The section of a choice of one spider in each class, see the module.

        Parameters:
            choice : The spider chosen in each class, keyed by the class.
        """
        graph = self.graph
        read = lambda s: choice.get(self.classes[s], s)
        dom_wires, box_wires, cod_wires = graph.wires
        box_wires = [(tuple(map(read, src)), tgt) for src, tgt in box_wires]
        cod_wires = tuple(map(read, cod_wires))
        needed, keep = set(cod_wires), set()
        needed |= {s for src, tgt in box_wires if not tgt for s in src}
        if not self.can_discard:
            keep = set(range(len(box_wires)))
        while True:
            more = {i for i, (_, tgt) in enumerate(box_wires)
                    if i not in keep and needed & set(tgt)
                    or not tgt}
            if not more - keep:
                break
            keep |= more
            needed |= {s for i in more for s in box_wires[i][0]}
        kept = sorted(keep)
        used = sorted(set(dom_wires) | set(cod_wires) | {
            s for i in kept for wires in box_wires[i] for s in wires})
        label = {s: k for k, s in enumerate(used)}
        relabel = lambda wires: tuple(label[s] for s in wires)
        return type(graph)(
            graph.dom, graph.cod, tuple(graph.boxes[i] for i in kept),
            (relabel(dom_wires), tuple(
                (relabel(box_wires[i][0]), relabel(box_wires[i][1]))
                for i in kept), relabel(cod_wires)),
            tuple(graph.spider_types[s] for s in used))

    def sections(self) -> list[Hypergraph]:
        """
        Every section, i.e. one for each choice of a spider in each class,
        hypergraph of the category or not.
        """
        classes = sorted(set(self.classes))
        members = [[s for s, c in enumerate(self.classes) if c == label]
                   for label in classes]
        return [self.section(dict(zip(classes, choice)))
                for choice in product(*members)]

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
        """ The labelled graph of the hypergraph, with a node per class. """
        graph = self.graph.to_graph()
        for spider, label in enumerate(self.classes):
            obj = self.graph.spider_types[spider]
            graph.add_node(("class", label), box="class")
            graph.add_edge(
                ("class", label), Node("spider", i=spider, obj=obj))
        return graph

    def __eq__(self, other) -> bool:
        if not isinstance(other, EHypergraph):
            return False
        if self.graph != other.graph:
            return False
        return is_isomorphic(
            self.to_graph(), other.to_graph(), lambda x, y: x == y)

    def __hash__(self) -> int:
        return hash((self.graph, tuple(sorted(
            self.classes.count(c) for c in set(self.classes)))))

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
    def strategy(cls, max_merges: int = 2, **params):
        """
        Generate e-hypergraphs: a hypergraph of the category, then up to
        ``max_merges`` equations between spiders of one type.

        Parameters:
            max_merges : The largest number of equations.
            params : Passed to :meth:`Hypergraph.strategy`.
        """
        from hypothesis import strategies as st

        if cls.category is None:
            raise NotImplementedError(
                f"No strategy implemented for {factory_name(cls)}.")

        @st.composite
        def ehypergraphs(draw):
            graph = cls(draw(Hypergraph[cls.category].strategy(**params)))
            for _ in range(draw(st.integers(0, max_merges))):
                i, j = draw(st.integers(0, 3)), draw(st.integers(0, 3))
                graph = graph.merge(*graph.pair(i, j))
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
    def extraction_monotonicity[I: Count, J: Count](
            cls, graph: Self, i: Var[int, I], j: Var[int, J]
    ) -> Equation[int]:
        """ An equation never makes the cheapest section more expensive. """
        before = cls.cost(graph.extract())
        after = cls.cost(graph.merge(*graph.pair(i, j)).rebuild().extract())
        return Equation(min(before, after), after)

    @axiom
    def extraction_discreteness[A: Obj[Ty], B: Obj[Ty]](
            cls, f: Hom[Self, A, B]) -> Equation[Hypergraph]:
        """
        The identity relation has one section, the hypergraph itself less
        the boxes nothing depends on.
        """
        discrete = type(f)(f.graph)
        return Equation(discrete.extract(), discrete.sections()[0])


Symmetric = EHypergraph[symmetric.Diagram]
Compact = EHypergraph[compact.Diagram]
Markov = EHypergraph[markov.Diagram]
Frobenius = EHypergraph[frobenius.Diagram]

LINEAR_BREAKS = (
    "extraction_soundness", "extraction_validity",
    "extraction_optimality", "extraction_monotonicity")
"""
The laws of extraction an e-hypergraph over a linear category breaks, i.e.
over a symmetric category that is not Markov, see
:data:`discopy.messages.LINEAR_SECTIONS`.
"""

for linear in (Symmetric, Compact):
    for law in LINEAR_BREAKS:
        setattr(linear, law, getattr(EHypergraph, law).failing(
            messages.LINEAR_SECTIONS))

for markovian in (Markov, Frobenius):
    markovian.congruence = EHypergraph.congruence.inapplicable(
        messages.NOT_DETERMINISTIC)

for linear in (Symmetric, Compact):
    linear.congruence = EHypergraph.congruence.failing(
        messages.INDUCTIVE_CONGRUENCE)
Symmetric.congruence_acyclic = EHypergraph.congruence.weaken(acyclic=True)
