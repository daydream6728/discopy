> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

cubic's review of d2673841:

> P3 discopy/python/finset.py:150: Computing every prefix with `sum(sizes[:i])` makes block permutation quadratic in the number of blocks, including identity permutations. Build the offsets incrementally in one pass.

> P2 discopy/matrix.py:555: `Matrix.basis` now forces numpy to build the array. Under the pytorch backend, a torch-dtyped class such as `Matrix[torch.float32]` gets a torch dtype passed to `np.array`, which raises a TypeError; it worked before. Build the array under the current backend, as `copy` does, so the `int64` fix for `basis(0, i)` stays.

> P2 discopy/tensor.py:889: This `setoid` only handles NumPy arrays, so `Box` data from the jax or pytorch backend still raises on hash and compares by identity. Flatten through the active backend instead, e.g. `with backend() as np:` and `np.array(data).reshape(-1).tolist()`, and drop the direct `numpy` import.

> P2 discopy/tensor.py:889: Flattening creates fresh NumPy scalars on each call, so a `Box` whose list-of-lists data contains `nan` no longer equals itself. Before this change identity made `f == f` hold. Compare the entries without re-creating them, or document that NaN entries are unsupported.

- [x] finset offsets in one pass
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 16:50 `basis` under the current backend, as `copy`
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 16:50 `setoid` on any backend's array, no direct numpy import
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 16:50 nan: reply, no code
