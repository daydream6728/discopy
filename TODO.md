> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `concrete`: `matrix.py`, `tensor.py`, `python/`, `interaction.py`, their tests.

- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 B3: `python.multiplicative` trace under default type checking, `trace(n > 1)`; B87's part: `test/python/multiplicative.py::test_trace` never calls the trace it names
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 B4: `finset.Function.permutation` ignores block structure
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 B32: `tensor.Box` equality and hash raise on array data
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 B36, purity part: `Matrix.__repr__` mutates numpy's global printoptions
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 B77 of #31: `Int(Matrix[bool]).braid` does `int @ int`
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 #88, basis part: `Matrix.basis(0, i)` infers `float64`
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 B88 of #31: `multiplicative.curry(n > len(dom))` silently truncates; `tensor.Functor.__call__` returns any `Dim` untouched
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 #168: `python.finset.Permutation` reprs as a bare tuple; `monoidal.Dim` cannot serialise
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 B87's finset part: `test/python/finset.py:17` pinned B1's inverse
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 15:55 CHANGELOG
