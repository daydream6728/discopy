# TODO

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

- [x] Reproduce [#359](https://github.com/rel-int/discopy-next/issues/359):
      `Z(0, 2)` and the one-layer diagram holding it have equal `setoid()` and
      compare unequal both ways.
- [x] Find the cause: `ZXBox.__eq__`, which asks `isinstance(other,
      type(self))` and so also leaves every ZX box unhashable.
- [x] Delete it and read equality off `cat.Box.setoid` like every other box.
- [x] Restore `test_to_pyzx`'s round trip to the spider, as #358 could not,
      and test the law on `Z`, `X`, `H`, `And` and `Or`.
- [x] Check `zw`'s own `__eq__` overrides: same law broken, different cause —
      filed rather than fixed here.
- [x] `CHANGELOG.md`.
- [x] `pflake8`, `pylint`, `pytest test/optyx/` with the extras and the full
      suite with `--skip-extra`.
