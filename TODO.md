# TODO

> here's a copy of the categorical deep learning paper, let's first make sure we align on how to turn these architecture diagrams into implementation

Decided live (toumix, 2026-10-19, recorded on [#121](https://github.com/rel-int/discopy-next/issues/121#issuecomment-6268851666)): parameters both as Para wires and as shared modules, folds as functors on data as diagrams, and first a notebook reproducing the paper on today's discopy-next.

- [x] `docs/notebooks/categorical-deep-learning.md`: constraints (H.1, H.3, C.1 as orbits), Para (Figs. 2–4, tying as `reparam` by `copy`), folds as functors (Figs. 10 and 12, equations (1)–(4)), unfolds as feedback (Figs. 11, 13, 14), Fig. 1's five cells
- [x] every gap the notebook hits filed as an issue, linked from #121: #124 (a module holding parameters), #125 (constant streams); found on the way, #123 (`Ty.name` is the class name)
- [x] linked from `docs/index.rst`, `CHANGELOG.md`, notebook check green
