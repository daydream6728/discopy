> @"/root/.claude/uploads/874612a5-721c-54a1-8e46-f2c92baf5442/d3f0da88-1705.07918v1.pdf" We need an implementation of contextual fraction in discopy.quantum, reproduce the examples from the paper.

The attached paper is Abramsky, Barbosa & Mansfield, [The contextual fraction as a measure of contextuality](https://arxiv.org/abs/1705.07918) (PRL 119, 050504, 2017).

- [x] `discopy.quantum.contextuality`: `Scenario`, empirical `Model` and `Inequality`, the incidence matrix, the linear program (3) for the (non-)contextual fraction, the decomposition (2) and the Bell inequality of Theorem 1 from the dual program (7)
- [x] quantum empirical models: local measurement circuits on a state, evaluated as channels
- [x] the operations of Theorem 2: mixing, choice `&`, product `@`, relabelling
- [x] tests reproducing Tables I, II and III, the maxima (14) and (15), Proposition 4 and Theorems 1 and 2
- [WIP] @session_012vx8TovHEkAieTr5eN2Ab5-2026-10-22 20:05 notebook reproducing Figure 1 and the tables; api docs, bibliography, `CHANGELOG.md`, `scipy` in the `quantum` extra
