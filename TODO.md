> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Batch 2 of the triage of #31's leftover bugs, `quantum.tk`, each checked with the numerical round
trip of `test/quantum/tk.py`:

- [ ] T22: `to_tk` moves a measured bit to the end of the bits, not to its wire: `Ket(1) @ Ket(0) >> qubit @ Measure() >> Measure() @ bit`
- [ ] T23: `to_tk` moves a `Bits(0)` left of an existing bit twice, by renaming and by a post-processing swap: `Ket(1) >> Measure() >> Bits(0) @ bit`; `test/quantum/tk.py:37` asserts that swap
- [ ] T24: `from_tk` makes a gate's qubits adjacent from their original indices, not their current positions: `CCX(2, 0, 1)`
- [ ] CHANGELOG
