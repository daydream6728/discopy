# #389, cubic's first round

> P2: These flag cases cannot fail. `==` ignores `is_conj` and
> `is_gate_dagger`, so a `__repr__` that drops the flag still passes.
> P2: `Create.__repr__` writes `internal_states` with `!r`, so numpy arrays
> serialize as `array([...])`.
> P2: This overstates the fix: public `classical.BitControlledPhaseShift` and
> `ClassicalFunction` still inherit generic channel/CQMap representations.
> P2: These representations are not evaluable for supported SymPy parameters.
> P2: `Observable` representations containing a function are not evaluable.
> P3: `Scalar(float('inf'))` now renders as `optyx.qubits.Scalar(inf)`.
> P3: Add an `### Added` entry for the 13 new public attributes.

- [x] `test_what_equality_ignores`, which reads back what `==` does not —
      mutation-checked by dropping `is_conj` from `BBS.__repr__`
- [x] `photonic.listed`, so an internal state prints as a list of numbers
- [x] `__repr__` for `BitControlledPhaseShift` and `ClassicalFunction`
- [x] `CHANGELOG.md`: the function boxes said plainly, and an `### Added` entry
- [x] answer the sympy and `inf` findings with the measurement on `main`
- [ ] re-run the checks
