> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

- [x] B40 (fable README claim table): the `--skip-extra` contract is broken by unguarded torch/jax imports in `test/tensor.py`; the pyzx guards ignore the version pin
- [x] B41: the coverage gate counts the test files themselves
- [x] B42: tests that cannot fail in `test/cat.py`, `test/markov.py`, `test/readme.py`
- [x] B43: nine modules have no test file; `test/test_para.py` naming drift. `test/para.py` is on `main`, `test/quantum/gates.py` too; new: `config`, `messages`, `python/function`, `grammar/cfg`, `grammar/thue`. Left out: `abc` and `quantum/pennylane`, whose mirrored names shadow the stdlib `abc` and the `pennylane` package under pytest's default `prepend` import mode (a decision), and `grammar/dependency`, whose one honest test is B30's, the grammar agent's
- [x] B45: self-contradictory and type-only error messages, the stale `pytest_plugin` pointer, `quantum.CY` (only if it exists unexported)
- [x] B84 of #31: `post.py` dying before `record()` leaves `clean` unset; the discopy/discopy#679 guard reads `steps.review.outcome` only: gone on `main`, `.github/style-review/` and its hand-over were retired by discopy/discopy#708 (`cd97339b`), and `benchmark_comment.mismatch` was fixed by #205
- [x] B87 of #31, circuit part: `test/quantum/circuit.py` skipped whole without torch; `test_CCX_decompose` leaks `np.set_printoptions`; `test_grad_basic`/`test_Sum` compare the int `0` to `0`
- [x] B88 of #31, static part: `uv_build` in `CONTRIBUTING.md` and the dead `[tool.uv.build-backend]`; `persist-credentials: false` claim; `pytest .github/tests/*.py` needs `--import-mode=importlib`; stray root `readme.py`; CHANGELOG `Ty.name` line; `docs/conf.py` mocks `sympy` and `pytket`. Already on `main`: `pytest .github/tests/*.py` passes without the flag since discopy/discopy#708 took the style-review tests, and the `Ty.name` line went in `418c6d02`
- [x] `discopy/autonomisation.gif` and `discopy/snake-removal.gif` tracked inside the package
- [x] CHANGELOG
