> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `hypergraph`, bullets of [#31](https://github.com/rel-int/discopy-next/issues/31) and [#168](https://github.com/rel-int/discopy-next/issues/168):

- [x] B50: `Hypergraph` equality and hash ignore the type of a scalar spider
- [x] B66: `Hypergraph.depth()` is two edges short when the path starts at a state
- [x] B82, sum part: `(f + g).to_map()` and `.to_hypergraph()` die with `no attribute 'zero'`
- [x] #168: `Hypergraph` repr prints its class parameter by bare `__name__` (already fixed on `main` by 0aec5eb)
- [x] #168: `CMap` repr hardcodes the `"cmap.CMap["` prefix
- [x] B88, cmap/hypergraph part: message-less `ValueError`/`AxiomError`s get messages
- [ ] B87, cmap part: `test/cmap.py:206` asserts truthiness; `test_curry_is_wiring_only_when_the_category_is_rigid` expects a failure
