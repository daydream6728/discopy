> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `concrete`: `matrix.py`, `tensor.py`, `python/`, `interaction.py`, their tests.

- [x] already fixed on main by #84 (879dac9): B3: `python.multiplicative` trace under default type checking, `trace(n > 1)`; B87's part: `test/python/multiplicative.py::test_trace` never calls the trace it names
- [x] B4: `finset.Function.permutation` ignores block structure
- [x] B32: `tensor.Box` equality and hash raise on array data
- [x] B36, purity part: `Matrix.__repr__` mutates numpy's global printoptions
- [x] already fixed on main, `Int(Matrix[bool]).ob` is `Ty[Nat]` and `test/interaction.py::test_trace_Matrix` braids it: B77 of #31: `Int(Matrix[bool]).braid` does `int @ int`
- [x] #88, basis part: `Matrix.basis(0, i)` infers `float64`
- [x] B88 of #31: `multiplicative.curry(n > len(dom))` silently truncates; `tensor.Functor.__call__` returns any `Dim` untouched
- [x] `Dim` part already fixed on main by #182 (ff0d9f70); the `Permutation` repr is left to USER, it is what `group` prints: #168: `python.finset.Permutation` reprs as a bare tuple; `monoidal.Dim` cannot serialise
- [x] already fixed on main by #193 (f9585742): B87's finset part: `test/python/finset.py:17` pinned B1's inverse
- [x] CHANGELOG
