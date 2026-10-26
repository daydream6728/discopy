> P2: This test fails with `ModuleNotFoundError` in environments that run the test file without the optional SymPy dependency. Guard the import like the existing gradient tests so the test is skipped when SymPy is unavailable. (test/quantum/zx.py)
>
> P2: This `importorskip` gates unrelated bubble coverage on the optional SymPy dependency. Split the symbolic substitution/lambdify assertions into a SymPy-specific test, so serialization, dagger, and saturation checks still run in the minimal dependency configuration. (test/markov.py)
>
> P2: These new circuit and ZX bubbles lose tensor-bubble state through inherited operations. `dagger()` drops a custom `func`, while `subs()` and `lambdify()` drop `is_dagger`; preserve those fields in the level-specific implementation or shared tensor bubble. (discopy/quantum/circuit.py)

(cubic-dev-ai)

- [ ] guard sympy in `test/quantum/zx.py::test_Bubble_grad`
- [ ] split the sympy assertions of `test/markov.py::test_Bubble_flags` into their own test
- [ ] circuit and zx bubbles: keep `func` through dagger, `is_dagger` through subs and lambdify, or answer it is #330's
