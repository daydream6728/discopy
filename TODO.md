# TODO

> phase 6

Phase 6 of the approved purification plan: the python carriers join the
matrix.

The laws, stated first per PROPTEST.md:

- [ ] `python.multiplicative.Function` is a closed symmetric Markov semantic carrier over the one-type universe `int`: its inherited axioms hold extensionally, i.e. up to an `equation_factory` probing both sides on canonical arguments, recursing through exponentials with canonical callables.
- [ ] `python.additive.Function` is a symmetric semantic carrier: tag-relabelling functions lifted from `finset`, compared extensionally on every tag. Its trace is Elgot iteration, partial, and `SymmetricCategory` states no trace law, so none applies.
- [ ] Neither carrier has a dagger on generated functions (`additive` only swaps have one): the dagger laws are inapplicable, like `finset.Function`.
- [ ] Strategies: a `Types` object carrier drawing `(int,) * n`, output-selection functions for multiplicative, finset tag maps for additive; reach pinned in the module test files.
- [ ] A closure neither reprs nor pickles: those cells are expected failures.
- [ ] Enrol both in `CARRIERS`; record any counterexample per PROPTEST.md.
- [ ] Delete what the matrix subsumes in `test/python/`; guardrails green, CHANGELOG updated, TODO deleted.
