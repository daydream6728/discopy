# TODO

> execute phase 5

Phase 5 of the approved purification plan: the tensor carriers join the
matrix.

The laws, stated first per PROPTEST.md:

- [ ] `tensor.Dim` is the object monoid: it inherits the type laws with `Dim(1)` as unit.
- [ ] `tensor.Diagram` is a free frobenius carrier over `Dim`: it inherits every frobenius diagram axiom unchanged, and the ad-hoc properties (repr, pickle, tree, drawing, conversion, eq/hash, normal form) with it.
- [ ] `Tensor[int]` is a semantic carrier like `Matrix[int]`: the axioms hold on the nose on arrays, stating which inherited declarations (`.failing`, `.inapplicable`) carry over from `Matrix` and which `Tensor` corrects.
- [ ] Strategies: `Dim.strategy`, `Tensor.strategy`, and box generation for `tensor.Diagram`; reach pinned in `test/tensor.py::test_strategy`.
- [ ] Enrol the carriers in `CARRIERS`; any counterexample found is recorded per PROPTEST.md.
- [ ] Delete the equational bits of `test/tensor.py` the matrix subsumes.
- [ ] Guardrails green, CHANGELOG updated, TODO deleted.
