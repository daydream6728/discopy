# TODO

> nah let's drop that PR for now and open a fresh draft in discopy-next, reuse the property-based testing machinery from daydream's PR as much as possible so you can start by writing down the axioms that ehypergraphs should respect

Context: "that PR" is [discopy#730](https://github.com/discopy/discopy/pull/730), the 1255-line
`discopy.ehypergraph`; "daydream's PR" is [rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1),
which this branch is stacked on. Earlier in the same session it was agreed that an e-hypergraph can be a
`hypergraph.Hypergraph` with an equivalence relation on its spiders, checked on #730's own example.

- [x] State the axioms of `ehypergraph.EHypergraph` in the sequent DSL of `discopy.axioms`
- [x] Implement them on top of `Hypergraph`, small enough to be the specification: `merge`, `rebuild`,
      `sections`, `extract` by brute force, `then`, `tensor`, `dagger`, equality up to isomorphism
- [x] `EHypergraph.strategy`, so that the symmetric, compact, Markov and Frobenius aliases enrol in the
      matrix: 101 laws pass, 2 skipped, 10 declared broken with their reasons
- [ ] Settle with the human what `s ~ t` means over a linear category, i.e. symmetric but not Markov,
      where no section of a nontrivial relation is a hypergraph of the category (`LINEAR_SECTIONS`)
- [ ] Settle with the human whether congruence on a feedback loop should be coinductive
      (`INDUCTIVE_CONGRUENCE`)
- [ ] Rewrite rules: matching a hypergraph in an e-hypergraph, adding the right-hand side and merging
- [ ] A fast extraction, checked against the brute-force one by `extraction_optimality`
