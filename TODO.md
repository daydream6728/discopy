# TODO

> go for phase 8.

Phase 8 of the approved purification plan: the interaction, stream and
para carriers join the matrix.

The laws, stated first per PROPTEST.md:

- [ ] `interaction.Diagram` over a symmetric traced base is the Int construction: a compact carrier whose objects are pairs and whose arrows are underlying arrows on the twisted boundaries, inheriting the compact laws up to the base's own equation.
- [ ] `stream.Stream` over a symmetric base is a feedback carrier whose equality is bisimulation bounded by finite unrolling: its laws hold `.modulo` unrolling a few steps.
- [ ] `para.Symmetric` over a symmetric base wraps arrows `dom @ param -> cod @ copar`: its laws hold up to the base's equation on the unwrapped arrows.
- [ ] Strategies for all three lift the base's, with boundaries respected; reach pinned in the module test files.
- [ ] Enrol what holds in `CARRIERS`; record any counterexample per PROPTEST.md; a wrapper holding closures is expected to fail pickling.
- [ ] Delete what the matrix subsumes in `test/`; guardrails green, CHANGELOG updated, TODO deleted.
