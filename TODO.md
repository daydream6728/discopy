# TODO

cubic's round on #424, verbatim:

> P2: This predicate makes identical infinities compare unequal because
> `inf - inf` is NaN. Preserve matching-infinity equality while keeping
> absolute tolerance unchanged, for example by using `np.allclose` with
> `rtol=0` and `equal_nan=False`.

It is right, and `[inf]` against `[inf]` is the one case where
`abs(a - b) <= tol` and the reading this head means come apart: the difference
is a NaN for a reason that is not a NaN amplitude.

- [x] Read the comparison with `np.allclose(rtol=0, atol=tol,
      equal_nan=False)`, which is the same absolute tolerance, the same NaN
      verdict and numpy's own reading of two infinities — and one call rather
      than a predicate of our own.
- [x] Pin `[inf]` against `[inf]` and against `[-inf]` in the test and the
      docstring, since that is what the round found.
