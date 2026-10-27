Fix rel-int/discopy-next#167 (python.finset.Function.then composes non-composable functions, silently or with IndexError) as the issue describes.

- [x] `Function.then` raises `AxiomError` on each adjacent pair whose `cod.n != dom.n`
- [x] regression test in `test/python/finset.py`
- [x] `CHANGELOG.md` line under Fixed
- [x] lint, pylint, suite
