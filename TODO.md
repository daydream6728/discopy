# TODO

cubic's review of this pull request, 2026-10-19, quoted:

> **6 issues found** across 8 files
> - test/utils.py:220 — P3: The `#775` here is an upstream issue, but a bare `#N` resolves to this repo. Qualify it as `discopy/discopy#775`.
> - discopy/utils.py:470 — P3: The docstring suggests a box's `data` dict is left alone, but a dict with exactly the keys `factory`, `re`, `im` and tag `complex` is decoded to a complex number even inside `data`. [...] Document the reservation accurately.
> - discopy/quantum/gates.py:873 — P2: `Sqrt.from_tree` reuses `MixedScalar.from_tree`, which only reads `data`, so `is_dagger` is dropped on round-trip. [...]
> - CHANGELOG.md:1116 — P3: The enumeration omits `CRx` [...]
> - discopy/monoidal.py:215 — P3: The note uses `object` as the non-transparent example, but `object` is a class and now round-trips through `factory_name`; change the example to `object()` [...]
> - discopy/monoidal.py:300 — P2: `generator_repr` sends nested classes through `factory_name`, which drops their enclosing class from the name. [...]

- [ ] qualify `#775` in `test/utils.py`
- [ ] say in `decode_complex` which dictionary is reserved
- [ ] `Sqrt.from_tree` reads `is_dagger`, with the conjugated root in the round-trip test
- [ ] `CRx` in the changelog entry of discopy/discopy#793
- [ ] `object()` as the example in `List`'s note
- [ ] nested classes: answered on the thread, `factory_name` is the library-wide printer and not this pull request's to change
