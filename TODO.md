# TODO

🌙 Evening's prompt for the night of 2026-11-01, verbatim:

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

[next#422](https://github.com/rel-int/discopy-next/issues/422):
`misc.compare_arrays_of_different_sizes` ends in
`np.flatnonzero(np.abs(a[:n] - b[:n]) > tol).size == 0`, and every comparison
with a NaN is `False`, so a NaN is never counted as a difference —
`cmp([1, nan], [1, 2])` is `True` where `np.allclose` is `False`. A NaN is not
equal to itself, which is what `np.allclose`'s `equal_nan=False` says, so the
helper is wrong rather than lenient. `core/zw.py` states every ZW axiom with
this helper and `test/optyx/test_zw.py` checks 28 of them through it.

- [x] Read the difference strictly:
      `np.all(difference <= tol)`, where a NaN difference fails the
      comparison instead of passing it. The tolerance reading, the flatten and
      the truncation to the shorter array all stay as they are — testing for a
      NaN *before* the flatten breaks seven tests, the helper being called
      with scalars.
- [x] Drop `zw.has_nan` and the guard it
      serves in `ZBox.__eq__`: with a strict helper `ZBox(1, 1, [1, nan])` is
      already unequal to itself, and `STYLE.md`'s *never repeats itself* says
      one of the two goes. `has_nan` has exactly that one caller.
- [x] Invert the assertion of
      `test_zbox_equality_rejects_nan_amplitudes` that pins the defect, and
      say in its docstring what the helper now reads.
- [x] Run the whole of `test/optyx`, plus
      `pflake8`, `pylint`, `ruff` and the wide suite, and `CHANGELOG.md`.
