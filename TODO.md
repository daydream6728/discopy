> cubic's review of 5f96e730 (2026-10-23):
>
> P2: The documented and CI benchmark command silently skips this entire module because `pyzx` is not installed by the `dev` group. Add PyZX to the benchmark environment or run the benchmark with the `quantum` extra; otherwise no ZX measurements are collected.
>
> P2: `from_diagram` crashes on valid zero-legged green spiders because `Z` has no entry in `legs`. Handle an empty `legs` list by allocating an isolated spider (as the X branch already does).
>
> P2: `size` overcounts internal plain PyZX edges as Hadamard edges. Filter the edge count by `EdgeType.HADAMARD` in addition to excluding boundary edges.

- [x] the benchmark job runs `benchmark/test_zx.py` with pyzx 0.10.7, its full tail capped at 1000 gates so that every push to `main` stays cheap; CONTRIBUTING says it needs pyzx
- [x] `from_diagram` makes a zero-legged spider an isolated one, with a test
- [x] `size` counts only Hadamard edges of a PyZX graph, with a test
