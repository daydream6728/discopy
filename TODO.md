# TODO

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

- [x] Reproduce [#301](https://github.com/rel-int/discopy-next/issues/301): a
      functor that widens an atomic type sends `Swap(x, y) @ z` to one
      permutation and `Swap(x, y)` to a staircase of four.
- [x] Take the native-permutation branch of `symmetric.Functor.__call__`
      before the `Swap` one, so a swap is a permutation like any other.
- [x] Check `Functor.id` still sends a `Swap` to itself, and that a codomain
      with no `permutation_factory` still gets its `swap`.
- [x] Test the coherence in `symmetric`, `markov`, `compact` and `frobenius`.
- [x] `CHANGELOG.md`, the docstring of `symmetric.Functor` and its doctest.
- [x] `pflake8`, `pylint` and the full suite with `--skip-extra`.
