# TODO

> go for phase 4

Phase 4 of the approved purification plan: the drawing smoke property.

The laws, stated first per PROPTEST.md:

- [ ] For every diagram carrier, `to_drawing` preserves the boundary:
  `d.to_drawing().dom == d.dom.to_drawing()` and likewise for `cod`.
- [ ] For every diagram carrier, both backends render a generated diagram
  without a baseline: Matplotlib on Agg into an in-memory buffer, TikZ
  into a throwaway file.
- [ ] `proptest/test_drawing.py` implements both, over the carriers of the matrix.
- [ ] Any counterexample found is recorded per PROPTEST.md before it is debugged.
- [ ] Guardrails green, CHANGELOG and CONTRIBUTING updated, TODO deleted.
