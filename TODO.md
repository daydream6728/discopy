# TODO

> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Round 2, the orchestrating session's request, relayed:

> please fold #16 into #287 (it needs no ruling; #140's "each level prints its own wire" ruling and biclosed.Wire's docstring already decide it). [...] Fix: set `biclosed.Ty.generator_factory = Wire` in biclosed.py (closed.py:132 already does this for closed). Widen the plain-`cat.Ob` upgrade in `cast_wire` from `is Wire` to Wire subclasses, so `biclosed.Ty(cat.Ob('x'))` and a bare `monoidal.Wire` still read back. Add a test: equality True, the repr round-trips, and the old printed form reads back.

- [ ] #16: `biclosed.Ty.generator_factory = Wire`, `cast_wire` upgrades a plain `cat.Ob` or uncoloured `monoidal.Wire` for every level whose generators are wires, with a test
- [ ] CHANGELOG, full suite, pflake8, pylint, proptest cells of `biclosed`
