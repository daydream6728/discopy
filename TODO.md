# TODO

> analyze the review comments of the original property based testing PR on
> discopy/discopy (upstream) and let me know whether the comments are still
> relevant with this new architecture. if so, address the issues here locally.

The live round is cubic's 2026-08-26 review of #347 (7 findings); everything
older is resolved on the PR or superseded by this branch. Triage against this
tree:

- [x] `monoidal.Layer.strategy` unused `boundary_connected` — already removed
  in the phase-8 search-space work, nothing to do.
- [ ] `testing.Axiom.broken` scans `co_names` for the literal `"AxiomError"` —
  valid: `.failing` is now the only producer of brokenness, so set an explicit
  flag there and propagate it through `modulo`/`weaken`.
- [ ] `cat.Functor.strategy` declares `dom`/`cod` and ignores them — valid: no
  caller passes them, drop the parameters.
- [ ] `abc.Category.equation_factory` docstring names both alternatives
  `cls.equation_factory` — valid, restate the strict-vs-quotient choice.
- [ ] CHANGELOG "Added" describes the removed strict/setoid status system as
  shipped — valid, fold into the entry that removes it.
- [ ] `Matrix.strategy` ignores `dtype` — deliberate: integer entries are
  exact in every enrolled dtype where floats would make strict equations
  flaky; say so in the docstring.
- [ ] broken axioms can XPASS when 25 draws miss the counterexample — the
  ledger is this architecture's deterministic answer, but only 3 of the 16
  `.failing` declarations carry a record: falsify each of the rest and record
  the shrunk arguments in `proptest/test_counterexamples.py`.
