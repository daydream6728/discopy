> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

USER's ruling on B60 of #31, live on 2026-10-22:

> Fix now

- [x] B60: `symmetric.Functor` sends a `Permutation` to the codomain's `from_permutation`, so `Functor.id(level)(p) == p` on symmetric, markov, compact and frobenius
- [x] tests: the identity on four levels; non-atomic images equal the old staircase up to `Equation` and evaluate the same into `Matrix`
- [x] CHANGELOG `### Fixed` bullet
