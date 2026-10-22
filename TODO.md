> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `gates`: `quantum/gates.py`, box-level `quantum/circuit.py`, `test/quantum/gates.py`.

- [x] B10: `Controlled.array` ignores the dagger and the rotation of the gate it controls, so `Controlled(S).dagger()` is a numeric no-op
- [x] B11: `subs`/`lambdify` drop `distance` and `is_mixed`; `Sqrt.dagger` is unconjugated
- [x] B12: `U1.grad(mixed=False)` disagrees with the finite difference
- [x] B54: `Controlled.l`/`.r` are the conjugate, not the transpose; `CRz(.5).rotate()` crashes
- [x] B55: `circuit.Box(..., is_mixed=False).dagger()` and `.rotate()` come back mixed
- [ ] B82 (gates part): `QuantumGate` rejects a 2-D array or a symbolic list as `data`
- [ ] B68 (gates part): `Ket(True)` is `|0>+|1>`, a numpy-bool bitstring prepares the zero vector
- [ ] #176: gates with a constructor of their own raise on `delay()`
- [ ] #168: `Controlled` hardcodes its name in its repr, `Bits` returns `self.name` as repr
- [ ] CHANGELOG, full suite, pflake8, pylint, proptest cells
