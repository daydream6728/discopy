# TODO

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

- [x] Reproduce [#292](https://github.com/rel-int/discopy-next/issues/292):
      `And().dagger()` is `And(n=True)`, a one-bit undaggered gate, and both
      gates keep `bit ** n -> bit` whatever the flag says.
- [x] Reproduce [#293](https://github.com/rel-int/discopy-next/issues/293):
      `SWAP.to_tensor()` raises, a plain three-argument function having been
      set on the instance.
- [x] Give `And` and `Or` an `n`, read the types off the flag, and keep `n`
      through `dagger` and `conjugate`.
- [x] Carry the fix into `determine_output_dimensions`, which read `n` off
      `len(input_dims)` and so needed the wrong dom to be right.
- [x] Drop `swap_truncation`, its assignment and the array it read: a plain
      `diagram.Swap(bit, bit)` already evaluates to the swap.
- [x] Test the dagger against the conjugate transpose for `n = 2, 3`, and that
      `SWAP` evaluates.
- [x] `CHANGELOG.md`.
- [x] `pflake8`, `pylint`, `pytest test/optyx/` with the extras and the full
      suite with `--skip-extra`.
