# TODO

Prompt (toumix, 2026-10-23, verbatim):

> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Ruling on #164 (USER, 10-22, https://github.com/rel-int/discopy-next/issues/164#issuecomment-6349748865): one class, `abc.Nat`. A law's number variable is drawn from `Nat.strategy`, and `axioms.Count`/`MAX_COUNT` go. `Ty.__pow__`, `spiders` and the other `int` asserts accept anything with `__index__`.

---

- [x] #164: a law's number variable is an `abc.Nat` drawn from `Nat.strategy`; `axioms.Count` and `MAX_COUNT` go, `ehypergraph` and `test/axioms.py` follow
- [x] #164: `Ty.__pow__`, `spiders` and the other `int` asserts of `monoidal` and `frobenius` accept anything with `__index__`
- [x] the property matrix collects and passes the same cells as before
- [x] `CHANGELOG.md`
