# TODO

cubic's review of this pull request, 2026-10-19, quoted:

> **2 issues found** across 11 files
> - discopy/hypergraph.py:131 — P2: `Hypergraph` now inherits `DaggerCategory` unconditionally, so `Hypergraph[Function]` (over a category with no `dagger`) claims the dagger laws. [...]
> - discopy/abc.py:33 — P3: The module docstring still says `Category` states the involution and contravariance of its dagger, which this PR moves to `DaggerCategory`. [...]

- [ ] the module docstring of `abc` names `DaggerCategory` for the two dagger laws
- [ ] `Hypergraph`: answered on the thread, it claimed the same laws through `Category` before this merge
