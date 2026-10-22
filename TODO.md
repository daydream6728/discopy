> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `converters`: `quantum/tk.py`, `quantum/zx.py`, `quantum/pennylane.py`, `quantum/channel.py`, `Circuit.to_tn`/`measure`, their tests.

- [ ] B56 of #31: `to_tk` drops a permutation over mixed bit/qubit types; `test/quantum/tk.py:67` asserts the bug (B87)
- [ ] B57 of #31: `to_tk` drops `Discard(bit)`; backend `eval` returns the joint distribution at the wrong shape
- [ ] B23: `to_tk` dies on CCX/CY/CRy/CU1; `from_tk` crashes on U1/CU1
- [ ] B24: pennylane uses the removed `Operation.inv()` and scales by `_scale ** 2`
- [ ] B33: `to_tn` crashes on bit discards and non-destructive measures; classical `measure()` crashes
- [ ] B68 of #31, channel part: `Channel.then` checks the flattened `Dim` only; `CQ.__str__` prints a classical type as `Q(...)`
- [ ] B39 quantum part and #168: repr of a measure, `quantum.zx.Swap` reprs as `"SWAP"`, `quantum.channel.CQ` str-interpolates unqualified fields
- [ ] B44: quantum interop tests are phase-0 and structural-only: numerical tk round trip, zx translation of a non-zero-phase controlled gate
- [ ] CHANGELOG
