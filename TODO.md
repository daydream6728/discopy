> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Rulings: https://github.com/rel-int/discopy-next/issues/31#issuecomment-6351134408

- [ ] B41: tests for `ehypergraph` in `test/ehypergraph.py` that state what its docstrings promise, until `source = discopy` is back over the 98% `fail_under`; then the gate is on in CI
- [ ] Tests mirror `discopy/` under `--import-mode=importlib`: set it in the pytest config, move today's tests of `discopy/abc.py` and `discopy/quantum/pennylane.py` to `test/abc.py` and `test/quantum/pennylane.py`, shared test code from `test/fixtures`; CI collects exactly the same tests
