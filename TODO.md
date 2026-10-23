> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

T39b (found by triage, no issue of its own): `to_map`/`to_hypergraph` of `n` states followed by
a reversal built as swaps is superlinear, since each whiskered swap, a `Permutation` of the whole
width, goes through the functor wire by wire.

- [ ] `CMap.from_diagram` and `Hypergraph.from_diagram` read a `Permutation`'s `perm` directly
- [ ] a test of each in `test/cmap.py` and `test/hypergraph.py`
- [ ] a benchmark case in `benchmark/test_conversion.py`
- [ ] one `CHANGELOG.md` bullet
