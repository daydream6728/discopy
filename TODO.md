# TODO

> go for phase 7

Phase 7 of the approved purification plan: the quantum carriers join the
matrix — pure Python only, no tket, pennylane or NLP extras.

The laws, stated first per PROPTEST.md:

- [ ] `quantum.circuit.Circuit` is a free structural carrier: generated circuits over the qubit universe — a fixed gate pool plus kets and bras to reach any boundary — inherit their level's diagram axioms unchanged, and the ad-hoc properties with them.
- [ ] `quantum.zx.Diagram` is a free symmetric carrier over `PRO`: Z and X spiders with phases, H and swaps; `PRO` gains the strategy whose absence kept it out of the matrix.
- [ ] Strategies boundary-constrained so composable pairs and squares generate; reach pinned in the module test files.
- [ ] Enrol both in `CARRIERS`; record any counterexample per PROPTEST.md.
- [ ] Delete the equational unit tests the matrix subsumes in `test/quantum/`.
- [ ] Guardrails green, CHANGELOG updated, TODO deleted.
