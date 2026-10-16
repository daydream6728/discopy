# TODO

> nah let's drop that PR for now and open a fresh draft in discopy-next, reuse the property-based testing machinery from daydream's PR as much as possible so you can start by writing down the axioms that ehypergraphs should respect

Context: "that PR" is [discopy#730](https://github.com/discopy/discopy/pull/730), the 1255-line
`discopy.ehypergraph`; "daydream's PR" is [rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1),
which this branch is stacked on. Earlier in the same session it was agreed that an e-hypergraph can be a
`hypergraph.Hypergraph` with an equivalence relation on its spiders, checked on #730's own example.

- [ ] State the axioms of `ehypergraph.EHypergraph` in the sequent DSL of `discopy.axioms`, with the
      interface they quantify over documented and not yet implemented
- [ ] Settle with the human what `s ~ t` means where boxes are linear, i.e. below Markov, and so where
      `rebuild` is sound (see the question in the module docstring)
- [ ] Implement the interface on top of `Hypergraph`: `merge`, `rebuild`, `sections`, `extract`, `then`,
      `tensor`, equality up to isomorphism
- [ ] `EHypergraph.strategy`: a hypergraph from `Hypergraph.strategy`, then a few merges of spiders of
      one type, so that it enrols in the property matrix
- [ ] Run the matrix on the e-hypergraphs of every symmetric level, declare what breaks
- [ ] Rewrite rules: matching a hypergraph in an e-hypergraph, adding the right-hand side and merging
