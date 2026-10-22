> A parallel session is working on double-pushout rewriting for symmetric and hypergraph categories, but it claimed to have an idea for how to handle the planar case. This is something I thought about a long time ago but we got stuck, can you solve it? A strong test case would be a rewrite rule on the spiral diagram where you would need to unroll the spiral to find a match.

(USER, live, 2026-10-22. The parallel session is #224, DPO over `Hypergraph`; its idea for the planar
case was "a convex match plus an upward-planarity test of the hole".)

A diagram in a monoidal category is a planar map whose wires all point down: its `CMap`. The map
forgets the layering, so it is the diagram up to interchange, faithfully when the diagram is
connected (Delpeuch & Vicary, §8). A map is the map of a diagram iff a horizontal line can sweep
it top to bottom, meeting each box once with its inputs side by side. A box with inputs can always
go next once they are. A state goes into a gap of the line in its own face, at the gap where the
corners of that face still turn by a full turn on each side: each corner between two inputs or two
outputs turns by +1, the top of a state and the bottom of an effect by −1, an inner face sums to
+2 and the outer one to −2 (Bertolazzi et al. 1994). With that choice the sweep never gets stuck
on a map that has a layering. A match of a left side is an injective map morphism whose image,
contracted into a single box, leaves a map that still sweeps. Planar, unlike Frobenius, has
exactly one pushout complement per match: `monoidal.Match`, the diagram with a hole.

- [x] `CMap.sweep` and `CMap.is_progressive`; `CMap.to_diagram` sweeps when the category has no
  swaps, so a state left of a wire decodes again
- [x] `CMap.homomorphisms`, `CMap.match` yielding `monoidal.Match`, `CMap.rewrite`, `normalize`,
  `normal_form`
- [x] the spiral: three rules unwind `spiral(n)` from its centre to the empty diagram in `2n + 1`
  steps, from the spiral as drawn and from its normal form, where the counit sits at the bottom
- [x] planar-only tests: genus zero but not progressive (`cap >> swap >> cup` read as a monoidal
  map); caps that look nested in the spiral but can be pulled side by side, and those that cannot
- [x] docs, bibliography (Bertolazzi et al.), `CHANGELOG.md`
- [x] `pflake8`, `pylint` (`fail-under` 8.85 → 9.02: main 9.01, this branch 9.028 raw),
  `coverage run -m pytest` (1,576 passed, 119 skipped without the extras; every new line covered)
- [x] USER's read of the scope: a host must be connected, since a map does not say in which face a
  component touching nothing else lies; answered below

> create a discopy.spacial module (monoidal with scalar sliding) for which it is sound

(USER, live, 2026-10-22, answering "Keep connected hosts only?". A monoidal category is spacial when
a scalar `s : I -> I` slides past every morphism, `s @ f == f @ s` (Selinger's survey). A scalar can
then cross any wire, so a floating component lies in no face in particular, the map of a diagram is
the diagram up to the axioms, and matching on maps is sound for every host. Every braided category
is spacial, by naturality of the braid with the unit.)

- [WIP] @session_013PzWbScb5vkcym2x9JkEda-2026-10-22 20:00 `abc.SpacialCategory`, a monoidal category
  with the axiom `scalar_sliding`; `BraidedCategory` is one, so the matrix checks it on
  `matrix.Matrix[int]` and `EHypergraph`
- [WIP] @session_013PzWbScb5vkcym2x9JkEda-2026-10-22 20:00 `discopy.spacial`, the free spacial
  category: `Ty`, `Box`, `Diagram`, `Sum`, `Functor`, `CMap`, `Equation`
- [ ] `CMap.match` over a spacial category takes any host, and a closed pattern any union of
  floating components; over a planar one, connected hosts only as before
- [ ] tests: a scalar inside a circle is a scalar beside it; `f @ s` matches `f`; the
  `scalar_sliding` cells of the matrix pass
- [ ] docs (`syntax.rst`, the abc summary), `CHANGELOG.md`, checks
