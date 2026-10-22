> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

(toumix, 2026-10-22), with the rulings of the same day recorded at
https://github.com/rel-int/discopy-next/issues/56#issuecomment-6350435762 (decision 7) and
https://github.com/rel-int/discopy-next/issues/139#issuecomment-6350436673 (#139).

- [x] Decision 7: from compact up, `Hypergraph.from_box(g.r)` and `Hypergraph.rotate` give the transpose of `g`
- [x] The two lenient adjoint checks (`Hypergraph.__init__`, `CMap.validate_adjoint_types`) call `assert_isadjoint` in port order
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 20:35 The `pregroup.Ty` docstring says what its lenient check does raise
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 20:35 #139 (a): a decoded cup's or cap's legs go in the order their readers sit in the scan
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 20:35 #139 (b): the `to_hypergraph` and `to_map` docstrings document the quotient below braided
