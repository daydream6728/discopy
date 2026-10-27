# next#351 — `eval(repr(x)) == x` for the boxes of `discopy.optyx`

Prompt (daydream6728, scheduled, 2026-10-27):

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

🌙 Evening took [#351](https://github.com/rel-int/discopy-next/issues/351) as a
next-repo bug that needs no decision: STYLE.md's *"DisCoPy is transparent"*
says what is right, and `axioms.Testable.transparency` already states it as a
law. The fix is the convention `discopy/quantum/gates.py` already follows — a
box that narrows `__init__` prints its own constructor call.

- [x] `test/optyx/test_repr.py`, one cell per box, the instrument
- [x] `discopy/optyx/channel.py`: `Channel`, `CQMap`, `Measure`, `Encode`,
      `Discard`, `Observable`
- [x] `discopy/optyx/core/diagram.py`: `Mode` and `Bit` print their count
- [x] `discopy/optyx/qubits.py`
- [x] `discopy/optyx/photonic.py`
- [x] `discopy/optyx/classical.py`
- [x] `CHANGELOG.md`
- [x] `pflake8`, `ruff`, `ty`, `pylint`, `pytest --skip-extra`
