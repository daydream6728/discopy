"""
Planted bugs: each mutant rewrites one line of DisCoPy, for as long as a
``with`` block lasts, and says what kind of bug it plants and why some
samplers should miss it. The smallest counterexample of each, found by hand,
is in ``analysis.md``.
"""

import __future__
import inspect
import textwrap
from contextlib import contextmanager
from dataclasses import dataclass

from discopy import cat, hypergraph, monoidal


@dataclass(frozen=True)
class Mutant:
    """
    A one-line mutation of the method ``name`` of ``owner``: the source
    ``old`` replaced by ``new``.
    """
    name: str
    kind: str
    owner: type
    method: str
    old: str
    new: str
    why: str

    @contextmanager
    def applied(self):
        """ Rewrite the method in place, and restore it on exit. """
        raw = self.owner.__dict__[self.method]
        function = getattr(raw, "fget", None) or getattr(raw, "__func__", raw)
        source = textwrap.dedent(inspect.getsource(function))
        assert self.old in source, f"{self.name}: {self.old!r} not found"
        namespace = {}
        exec(compile(  # noqa: S102  pylint: disable=exec-used
            source.replace(self.old, self.new), inspect.getfile(function),
            "exec", flags=__future__.annotations.compiler_flag,
            dont_inherit=True), function.__globals__, namespace)
        setattr(self.owner, self.method, namespace[self.method])
        try:
            yield self
        finally:
            setattr(self.owner, self.method, raw)


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
        "merge_overlap", "< vs <=", monoidal.Layer, "merge",
        "if box_offset < offset:", "if box_offset < offset - 1:",
        "two layers merge although a box of the second starts one wire "
        "inside the codomain of a box of the first: only a sampler that "
        "draws adjacent boxes connected by a single wire can find it"),
    Mutant(
        "interlocked_traces", "coherence", hypergraph.Hypergraph, "trace",
        "for output, input_ in zip(outputs, inputs):",
        "for output, input_ in zip(outputs, inputs[::-1]):",
        "a trace of several wires feeds them back crossed, which "
        "the yanking of a single wire never shows: it takes a trace of "
        "two wires, as Selinger's interlocked traces"),
    Mutant(
        "identity_string", "missing edge case", cat.Arrow, "__str__",
        "' >> '.join(map(str, self.inside)) or f\"Id({self.dom})\"",
        "' >> '.join(map(str, self.inside))",
        "the identity prints as the empty string: only a sampler that draws "
        "the identity itself as a term finds it"),
)
""" The planted bugs, see :class:`Mutant`. """
