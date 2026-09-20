# TODO

> wait are you trying to make it compatible with python 3.14 since the
> beginning? i don't care about backward compatibility, neither for past
> python versions nor past discopy versions. I want this to be as clean
> as possible and not sacrifice ease of use/readability.

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-20 11:20 Bump to
      Python 3.14 (pyproject, lock, CI, hook) and confirm the full
      development environment syncs and the suites run on it
- [ ] Drop `from __future__ import annotations` everywhere and un-quote
      the forward references PEP 649 now resolves lazily; simplify
      `parse`'s guard accordingly
- [ ] Remove the past-discopy-version shims: `deprecated_alias` and the
      module `__getattr__`s, the `__setstate__` migration branches and
      the outdated-dumps `from_tree` warnings
- [ ] `ty check` green, `pflake8`, pytest, proptest fast profile,
      CHANGELOG
