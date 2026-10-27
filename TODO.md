Fix rel-int/discopy-next#167 (python.finset.Function.then composes non-composable functions, silently or with IndexError) as the issue describes.

- [ ] `Function.then` raises `AxiomError` on each adjacent pair whose `cod.n != dom.n`
- [ ] regression test in `test/python/finset.py`
- [ ] `CHANGELOG.md` line under Fixed
- [ ] lint, pylint, suite
