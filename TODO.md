# TODO

🌙 Evening's prompt for the night of 2026-11-01, verbatim:

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

[next#421](https://github.com/rel-int/discopy-next/issues/421):
`qubits.Z(0, 0).double().to_tensor().eval()` raises
`ValueError: cannot reshape array of size 2 into shape ()`, as do
`Z(0, 0, .25)` and `X(0, 0)`, while `Z(0, 1)`, `Z(1, 0)` and `Z(1, 1)` all
evaluate. A spider with no legs is a scalar and its tensor should have shape
`()`; the truncation yields two entries.

The offending box is `core.zw.ZBox(0, 0, [1, exp(2πiθ)])`, built by
`core.zx.Z.truncation`, so the two halves below are two readings of a legless
spider and each is settled by its own calculus rather than by the other's.

- [x] `core.zx.Z(0, 0, θ)` is the scalar
      `1 + exp(2πiθ)`, the sum its own spider definition gives, rather than a
      legless `zw.ZBox` carrying both amplitudes. Checked against pyzx, which
      the module's own docstring names as the oracle for the array of a `Z` or
      an `X`, and against the fused `Z(0, 1, θ) >> Z(1, 0)`. `X(0, 0, θ)` goes
      through `Z`'s truncation, so it comes with it.
- [x] `core.zw.ZBox(0, 0, amps)` reads
      its first amplitude, which is what the indexable branch of that same
      `truncation` already does and what all four of `test_zw.py`'s legless
      boxes state: the list branch was missing the index, `np.array([amps])`
      being a one-entry array only when `amps` is a bare number. It is also
      the only reading total on an infinite amplitude list.
- [x] Tests: the three symptoms of the
      issue in `test_qubit.py`, the pyzx and fusion oracles in `test_zx.py`,
      and the legless `ZBox` in `test_zw.py`. Docstrings saying what a legless
      spider is in each calculus.
- [x] Run `test/optyx`, the wide suite,
      `pflake8`, `pylint`, `ruff`, the changed modules' doctests, and
      `CHANGELOG.md`.
