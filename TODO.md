> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `levels`: `monoidal.py`, `rigid.py`, `traced.py`, `feedback.py`, `markov.py` and their tests.

- [ ] B18: rigid `Box.dagger()` silently resets `z`; the double dagger is not the box
- [ ] B19: an oversized trace silently succeeds; a negative trace recurses
- [ ] B25: heterogeneous-memory `feedback` is broken; `feedback.Diagram.discard` is uninitialised
- [ ] B27: `Id(x).width` raises on an empty `max()`
- [ ] B34: `rigid.nesting` never checks the two types have equal length
- [ ] B35: a failing `from_callable` leaks a monkey-patched `__call__`
- [ ] B39 (traced part) and #168: `traced.Trace` interpolates `str` instead of `repr` of its argument
- [ ] B86: `FollowedBy.__repr__` lacks the module prefix
- [ ] #168: `monoidal.Layer.__setstate__` restores the pre-normalisation cached `name`/`dom`/`cod`
- [ ] B88: `feedback.Copy`/`Merge`/`Permutation.delay` leave `time_step` at 0
- [ ] B88: `markov.Diagram.discard(x, n)` ignores `n`
