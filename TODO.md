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
- [WIP] @session_01MY1Vs5CEhXgYwJcDnNwx6i-2026-10-17 14:35 Matching: find the regions a left-hand side occurs at, for `rewrite` to apply a rule
      Prototyped with saturation, not on the branch yet: a critic found it drops the scalars of a
      right-hand side, and that it inherits the `rebuild` bug below
- [WIP] @session_01MY1Vs5CEhXgYwJcDnNwx6i-2026-10-17 14:35 A fast extraction, checked against the brute-force one by `extraction_optimality`
      Prototyped, not on the branch yet: exact (agrees with the brute force on 13k e-hypergraphs, tie-break
      included, validity being a local condition on each class), but its order of alternatives can be
      fooled into exponential time, and it only holds over symmetric categories
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
- [x] `extraction_rewrite` fails over symmetric categories when `f` has a wire passing through: rewriting
      all of `f` into `g` relates the boundaries so that an input of a section has no consumer, which a
      linear category cannot discard (found by the `dev` profile, `@reproduce_failure('6.164.0',
      b'AXicc2RyZECDjBgiQAgAay8FGA==')`)
      It failed over compact too: the relation holds in every section, so a right-hand side identifying two
      positions the region keeps apart destroys the original section. `rewrite` refuses what does not
      `fits`, and the law quantifies over `Rewrites`, two e-hypergraphs over one hypergraph

## Round 2

> monoidal egraphs go brrr

@toumix's prompt for the session that picked this pull request up from a handoff of the session that opened
it, whose next steps are the boxes above and below. It worked on a pull request into this branch, #92, which
@toumix asked to fold back here: "keep only one PR open".

- [x] Fix [#91](https://github.com/rel-int/discopy-next/issues/91), the multiplicative trace
      raising on any loop, then check `trace_uniformity` on `python.Function`
      Ported from next `main`'s #84, identical, with tests: uniformity along copy holds on `python.Function`,
      checked over `markov.Square` mapped into monotone Boolean functions, where the iteration is a least
      fixed point; it fails along a discard, whose loop need not terminate
- [ ] `rebuild` over a linear category merges the outputs of two congruent boxes that coexist, e.g.
      `a @ a >> m`, so that no section is valid: `Symmetric.from_diagram(a @ a >> m).rebuild().extract()`
      raises
- [ ] Propose the API of a coinductive `bisimulation` and ask the human to confirm it before building it
- [ ] Ask the human what strictness should mean for a merge, which is strict but not natural along a copy

