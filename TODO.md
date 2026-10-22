> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

- [ ] B70 of #31: `closed.Eval(X >> Y)` defaults left, as `Diagram.ev` and `Application.eval` do since discopy/discopy#560
- [ ] B70 of #31: `biclosed.Curry(f, n)` raises when `n` is not between zero and `len(f.dom)`
- [ ] B70 of #31: `Eval(x << y, left=False)` and `Coeval` with a side the exponential contradicts raise
- [ ] B88 of #31, para part: `para.Closed.curry` defaults `left=True`
- [ ] B86 of #31, closed part: `biclosed.Eval`/`Coeval` round-trip through `repr` and `dumps`
- [ ] #168: the `biclosed`/`closed` bubbles `Curry`, `Eval`, `Coeval` read back their trees, nested in a diagram too
- [ ] #177: `g(X('a')).eval().to_hypergraph()` does not send a constant to `map_term`
- [ ] CHANGELOG
