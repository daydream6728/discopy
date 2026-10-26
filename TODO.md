# Review round: cubic on cdc189c5

> P2 (discopy/tensor.py:1208): Function-bearing derivatives do not have a readable representation: `repr(Diff(..., func))` embeds Python's `<function ...>` form, so evaluating it raises a `SyntaxError` and gradient bubbles inherit the same broken representation. Format importable functions by module path, and handle non-importable callables consistently with the documented representation contract.

- [ ] `Diff` prints a named `func` by its import path, as `Bubble` does
