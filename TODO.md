> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `levels`: `monoidal.py`, `rigid.py`, `traced.py`, `feedback.py`, `markov.py` and their tests.

- [x] B18: rigid `Box.dagger()` silently resets `z`; the double dagger is not the box
- [x] B19: an oversized trace silently succeeds; a negative trace recurses
- [x] B25: heterogeneous-memory `feedback` is broken; `feedback.Diagram.discard` is uninitialised (already fixed on `main`: the memory of many wires feeds back, `test_feedback_with_a_memory_of_many_wires`, and `discard` moved to `markov.Diagram`, which builds it)
- [x] B27: `Id(x).width` raises on an empty `max()`
- [x] B34: `rigid.nesting` never checks the two types have equal length
- [x] B35: a failing `from_callable` leaks a monkey-patched `__call__`
- [x] B39 (traced part) and #168: `traced.Trace` interpolates `str` instead of `repr` of its argument (already fixed on `main`: `traced` is an alias of `feedback`, whose `Trace` reprs its argument, `test_trace_repr`)
- [x] B86: `FollowedBy.__repr__` lacks the module prefix (already fixed on `main`: it reprs with `factory_name`)
- [x] #168: `monoidal.Layer.__setstate__` restores the pre-normalisation cached `name`/`dom`/`cod`
- [x] B88: `feedback.Copy`/`Merge`/`Permutation.delay` leave `time_step` at 0 (left out: a structural box delays its types, which time step it reads is a choice, reported)
- [x] B88: `markov.Diagram.discard(x, n)` ignores `n` (already fixed on `main`: `discard` takes no `n`)
