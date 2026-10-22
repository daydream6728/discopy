> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `concrete`: `matrix.py`, `tensor.py`, `python/`, `interaction.py`, their tests.

- [ ] B3: `python.multiplicative` trace under default type checking, `trace(n > 1)`; B87's part: `test/python/multiplicative.py::test_trace` never calls the trace it names
- [ ] B4: `finset.Function.permutation` ignores block structure
- [ ] B32: `tensor.Box` equality and hash raise on array data
- [ ] B36, purity part: `Matrix.__repr__` mutates numpy's global printoptions
- [ ] B77 of #31: `Int(Matrix[bool]).braid` does `int @ int`
- [ ] #88, basis part: `Matrix.basis(0, i)` infers `float64`
- [ ] B88 of #31: `multiplicative.curry(n > len(dom))` silently truncates; `tensor.Functor.__call__` returns any `Dim` untouched
- [ ] #168: `python.finset.Permutation` reprs as a bare tuple; `monoidal.Dim` cannot serialise
- [ ] B87's finset part: `test/python/finset.py:17` pinned B1's inverse
- [ ] CHANGELOG
