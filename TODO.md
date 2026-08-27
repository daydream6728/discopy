# TODO

> from now on keep maintaining the BUGS.md file. engage phase 9

Phase 9 of the approved purification plan: the hopf carrier joins the
matrix. Any bug found lands in BUGS.md in the same commit as its fix or
declaration, from now on.

The laws, stated first per PROPTEST.md:

- [ ] `Intertwiner[Double(Algebra.cyclic(2))]` is a ribbon carrier whose structural laws (category, monoidal) hold on the nose as tensor diagrams, and whose ribbon laws — hexagons, braid naturality, twist, snakes, pivotality, Reidemeister, traces — hold `.modulo` evaluation, rounded against float noise.
- [ ] The spider and copy families are inapplicable: a representation category has no chosen spiders.
- [ ] Strategies: `Representation` draws tensor products of the toric-code atom `e ⊕ m`; `Intertwiner` draws layered braids, twists and genuine intertwiner boxes — diagonal anyon projections and zero maps — never a data-less box, so every law can evaluate.
- [ ] Enrol in `CARRIERS`; record any counterexample per PROPTEST.md and log every find in BUGS.md.
- [ ] Delete what the matrix subsumes in `test/hopf.py`; guardrails green, CHANGELOG updated, TODO deleted.
