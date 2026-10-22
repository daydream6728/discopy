> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

- [ ] B40 (fable README claim table): the `--skip-extra` contract is broken by unguarded torch/jax imports in `test/tensor.py`; the pyzx guards ignore the version pin
- [ ] B41: the coverage gate counts the test files themselves
- [ ] B42: tests that cannot fail in `test/cat.py`, `test/markov.py`, `test/readme.py`
- [ ] B43: nine modules have no test file; `test/test_para.py` naming drift
- [ ] B45: self-contradictory and type-only error messages, the stale `pytest_plugin` pointer, `quantum.CY` (only if it exists unexported)
- [ ] B84 of #31: `post.py` dying before `record()` leaves `clean` unset; the discopy/discopy#679 guard reads `steps.review.outcome` only
- [ ] B87 of #31, circuit part: `test/quantum/circuit.py` skipped whole without torch; `test_CCX_decompose` leaks `np.set_printoptions`; `test_grad_basic`/`test_Sum` compare the int `0` to `0`
- [ ] B88 of #31, static part: `uv_build` in `CONTRIBUTING.md` and the dead `[tool.uv.build-backend]`; `persist-credentials: false` claim; `pytest .github/tests/*.py` needs `--import-mode=importlib`; stray root `readme.py`; CHANGELOG `Ty.name` line; `docs/conf.py` mocks `sympy` and `pytket`
- [ ] `discopy/autonomisation.gif` and `discopy/snake-removal.gif` tracked inside the package
- [ ] CHANGELOG
