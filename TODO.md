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
- [ ] USER's read of the scope: a host must be connected, since a map does not say in which face a
  component touching nothing else lies; maps that record faces are a follow-up
