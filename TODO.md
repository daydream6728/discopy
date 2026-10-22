> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `core` (`cat.py`, `utils.py`, `abc.py`, `test/cat.py`, `test/utils.py`):

- [x] B63 of #31: `utils.rmap` rebuilds an ndarray with its shape constructor, recurses forever on `str` data, and `Box.subs`/`rsubs` parse `*args` in incompatible shapes
- [x] #118: `cat.Box.subs`/`lambdify` rebuild `type(self)(name, dom, cod, data=..., is_dagger=...)` and lose what a subclass carries (`z`, `Word`'s argument order, `time_step`)
- [x] B61 of #31: `to_staircases`, `Layer.merge`, `foliation()`, `depth()` and `Functor.id` rebuild bubbles through `cod.bubble(*args, dom=, cod=)`, dropping `name` and drawing flags
- [x] B39/B86 of #31, the `cat.Bubble` part: `repr` and `to_tree` drop `name` and `method`
- [x] B88 of #31, `Functor.__eq__` ignores `dom`
- [x] B88 of #31, `abc.MonoidalCategory.tensor` is declared a classmethod while every implementation is an instance method
- [x] B88 of #31, the six message-less `ValueError`s in `abc.py`
- [x] B88 of #31, `Sum` builds its `name` eagerly, if it can be made lazy without changing public behaviour
- [x] `CHANGELOG.md`
