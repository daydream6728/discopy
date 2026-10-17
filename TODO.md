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
- [x] Settle with the human what `s ~ t` means over a linear category. @toumix, verbatim:
      > Yeah it doesn't make sense to equate two wires in an existing symmetric diagram but what does make
      > sense is a ehypergraph which holds a monogamous acyclic hypergraph and then applies a rewrite rule to
      > equate one subdiagram to a given RHS, adding that RHS to the ehypergraph and declaring equality of its
      > domain and codomain
- [x] `rewrite(region, dom, cod, rhs)` records the
      region and the right-hand side as alternatives; a section chooses a side of each, so that extraction holds
      over linear categories and `LINEAR_SECTIONS` goes
- [ ] Settle with the human whether congruence on a feedback loop should be coinductive
      (`INDUCTIVE_CONGRUENCE`). @toumix, verbatim:
      > Using coinduction would be awesome! I expect that the rebuild should work fine as an iterator so you
      > could unroll a feedback loop as many times as needed. Not sure if it makes sense to use coinduction to
      > "prove" anything about Python though?
- [ ] Matching: find the regions a left-hand side occurs at, for `rewrite` to apply a rule
- [ ] A fast extraction, checked against the brute-force one by `extraction_optimality`
- [x] Mark the maps the trace is uniform along. @toumix, verbatim:
      > can we add an extra boolean attribute "strict" which characterises for which maps the uniform axiom holds?
      `is_strict` on traced diagrams and `trace_uniformity` along copy, declared failing on the free
      categories; checking it on `python.Function` waits on
      [#91](https://github.com/rel-int/discopy-next/issues/91), its multiplicative trace raising on any loop
- [x] State the premise of uniformity as a shape. @toumix, verbatim:
      > I disagree with “no way to state an implication”, this is what shapes do! eg if f g h are composable then associativity
      > try to do the same with this uniformity axiom

      `markov.Square[C]` draws commuting squares by construction; `trace_uniformity_written` holds on
      every free traced Markov category but the hypergraph ones, where no square is drawn
- [ ] `extraction_rewrite` fails over symmetric categories when `f` has a wire passing through: rewriting
      all of `f` into `g` relates the boundaries so that an input of a section has no consumer, which a
      linear category cannot discard (found by the `dev` profile, `@reproduce_failure('6.164.0',
      b'AXicc2RyZECDjBgiQAgAay8FGA==')`)
