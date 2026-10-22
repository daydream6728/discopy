> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `core` (`cat.py`, `utils.py`, `abc.py`, `test/cat.py`, `test/utils.py`):

- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 16:02 B63 of #31: `utils.rmap` rebuilds an ndarray with its shape constructor, recurses forever on `str` data, and `Box.subs`/`rsubs` parse `*args` in incompatible shapes
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 16:02 #118: `cat.Box.subs`/`lambdify` rebuild `type(self)(name, dom, cod, data=..., is_dagger=...)` and lose what a subclass carries (`z`, `Word`'s argument order, `time_step`)
- [ ] B61 of #31: `to_staircases`, `Layer.merge`, `foliation()`, `depth()` and `Functor.id` rebuild bubbles through `cod.bubble(*args, dom=, cod=)`, dropping `name` and drawing flags
- [ ] B39/B86 of #31, the `cat.Bubble` part: `repr` and `to_tree` drop `name` and `method`
- [ ] B88 of #31, `Functor.__eq__` ignores `dom`
- [ ] B88 of #31, `abc.MonoidalCategory.tensor` is declared a classmethod while every implementation is an instance method
- [ ] B88 of #31, the six message-less `ValueError`s in `abc.py`
- [ ] B88 of #31, `Sum` builds its `name` eagerly, if it can be made lazy without changing public behaviour
- [ ] `CHANGELOG.md`
