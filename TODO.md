# TODO

> analyze the entire test suite and eliminate redundant tests that are
> now absorbed by property testing. the diff should be down to at least
> +8k-4k

- [x] Inventory every
      unit test against the matrix: a law an axiom cell states, a
      roundtrip the `Serialisable` axioms state, a construction smoke
      the strategy draws — cut those, keep behaviours, error cases and
      recorded regressions
- [x] Measure the diff against `main` down to at most +8k insertions
      and at least -4k deletions
- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-29 Validate: ruff, ty, pytest, fast + dev matrix, CHANGELOG, close
