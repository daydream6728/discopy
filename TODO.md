> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

(toumix, 2026-10-23)

Decision 8b, ruled on #56 (https://github.com/rel-int/discopy-next/issues/56#issuecomment-6350435762): one decoder for `Hypergraph` and `CMap`.

- [x] one scan-and-swap decoder that `Hypergraph.to_diagram` and `CMap.to_diagram` both call, with no change of output
- [x] check `CMap.sweep`/`encode` (#273) against it, and cover them if they decode
- [x] compare every decoded diagram before and after, layer for layer, on `test/fixtures/diagrams.py` and random diagrams from monoidal to frobenius
- [x] a test, the changelog line
