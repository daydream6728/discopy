"""
Planted bugs: each mutant rewrites one line of DisCoPy, for as long as a
``with`` block lasts, and says what kind of bug it plants and why some
samplers should miss it. The smallest counterexample of each, found by hand,
is in ``analysis.md``.
"""

import __future__
import inspect
import textwrap
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass

from discopy import abc, cat, hypergraph, monoidal


ORIGINALS = {}
""" The original method of each mutant applied, by mutant. """


@dataclass(frozen=True)
class Mutant:
    """
    A one-line mutation of the method ``name`` of ``owner``: the source
    ``old`` replaced by ``new``, then wrapped by ``wrap`` if the method is,
    e.g. a trace by :func:`discopy.abc.keyword_form`.
    """
    name: str
    kind: str
    owner: type
    method: str
    old: str
    new: str
    why: str
    wrap: Callable | None = None

    @contextmanager
    def applied(self):
        """
        Rewrite the method in place, its source read and compiled in its own
        module, under the decorators that source states, and restore it on
        exit.
        """
        raw = self.owner.__dict__[self.method]
        function = inspect.unwrap(
            getattr(raw, "fget", None) or getattr(raw, "__func__", raw))
        source = textwrap.dedent(inspect.getsource(function))
        assert self.old in source, f"{self.name}: {self.old!r} not found"
        namespace = {}
        exec(compile(  # noqa: S102  pylint: disable=exec-used
            source.replace(self.old, self.new), inspect.getfile(function),
            "exec", flags=__future__.annotations.compiler_flag,
            dont_inherit=True), function.__globals__, namespace)
        mutated = namespace[self.method]
        ORIGINALS[self] = raw
        setattr(self.owner, self.method,
                mutated if self.wrap is None else self.wrap(mutated))
        try:
            yield self
        finally:
            setattr(self.owner, self.method, raw)
            del ORIGINALS[self]

    @contextmanager
    def reverted(self):
        """
        Restore the original method in a block inside :meth:`applied`, so
        that a counterexample is checked against the code without the bug.
        """
        mutated = self.owner.__dict__[self.method]
        setattr(self.owner, self.method, ORIGINALS[self])
        try:
            yield self
        finally:
            setattr(self.owner, self.method, mutated)


MUTANTS = (
    Mutant(
        "layer_offsets", "off-by-one", monoidal.Layer, "boxes_and_offsets",
        "offset += len(box_or_typ.cod)", "offset += len(box_or_typ.dom)",
        "the offset of a box counts the inputs of the boxes on its left "
        "rather than their outputs: wrong only in a layer of several boxes "
        "where one on the left changes the width, which only a sampler that "
        "draws several boxes per layer can find"),
    Mutant(
        "permutation_convention", "wrong convention", hypergraph.Hypergraph,
        "from_diagram",
        "wires = tuple(range(len(box.dom))), (), tuple(box.perm)",
        "wires = tuple(range(len(box.dom))), (), tuple(sorted("
        "range(len(box.perm)), key=list(box.perm).__getitem__))",
        "a native permutation is read as its inverse: the same for every "
        "involution, e.g. a swap, so that only a cycle of three wires or "
        "more tells them apart"),
    Mutant(
        "layer_overlap", "< vs <=", hypergraph.Decoder, "place",
        "if offset < last_offset + len(last.cod):",
        "if offset < last_offset + len(last.cod) - 1:",
        "reading a hypergraph back as a diagram, a box joins the layer of the "
        "box before it although it starts on the last output of that box: "
        "only a sampler whose hypergraphs have two boxes in a row, the second "
        "reading the last output of the first, can find it"),
    Mutant(
        "left_trace", "coherence", hypergraph.Hypergraph, "trace",
        "(typ[n:], wires[:n], wires[n:]) if left",
        "(typ[n:], wires[:n], wires[n:]) if left and wires is self.dom_wires",
        "a trace on the left feeds back the last output rather than the "
        "first: the same for one output, and for outputs of one type wrong "
        "in the same way on both sides of every law, so that it takes a left "
        "trace whose outputs have two types, a rule 2b leaves out as "
        "admissible",
        abc.keyword_form),
    Mutant(
        "identity_string", "missing edge case", cat.Arrow, "__str__",
        "' >> '.join(map(str, self.inside)) or f\"Id({self.dom})\"",
        "' >> '.join(map(str, self.inside))",
        "the identity prints as the empty string: only a sampler that draws "
        "the identity itself as a term finds it"),
)
""" The planted bugs, see :class:`Mutant`. """
