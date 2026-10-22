> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

USER's ruling on #88 (10-22, [comment](https://github.com/rel-int/discopy-next/issues/88#issuecomment-6349549923)):

> USER ruled live (10-22): **normalise a subscript to the Python type**. `Matrix[np.int64] is Matrix[int]`; likewise float64 → float, complex128 → complex, bool_ → bool. A dtype names the ring of entries, so the bare class infers `Matrix[int]`, `Tensor[float]`, `tensor.Box[float]`. Other precisions (float32, int8, …) keep numpy's names. B9 and #162 land with it.

- [x] #88: a subscript by numpy's default-precision scalar type is the subscript by the Python type, for `Matrix` and `tensor.Diagram` and their subclasses; doctests respelled; pickles and trees of `Matrix[int64]` still load; bare `Matrix` enrollable in the property matrix
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 19:48 B9: `Matrix.map` with no dtype widens through `promote` rather than casting to the old dtype; `tensor.Diagram.eval()` with no dtype infers it from the boxes
- [ ] #162: `Testable.environment()` binds numpy's scalar types that builtins lacks, so an inferred `tensor.Box[float32]` reads back
