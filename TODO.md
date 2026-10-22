> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

USER's ruling on decision 8 of #56, live (10-22): "8a now, 8b next", recorded as https://github.com/rel-int/discopy-next/issues/56#issuecomment-6350435762:

> **Decision 8: 8a now, 8b next.** 8a scopes `interchange`/`normalize`/`snake_removal` to the planar levels, ports the 10 consumers of `Layer.boxes_and_types` and deletes it (#9). 8b, one decoder for `Hypergraph` and `CMap`, follows now that #285 has aligned them. Decision 3's levels go in parallel, since they touch functors and boxes, not the rewriting methods.

This branch is 8a only.

- [ ] `interchange`, `normalize`, `snake_removal`, `normal_form`: say in their docstrings that they are planar rewrites, scoped to the levels from `monoidal` to `rigid`, and split a foliated diagram into staircases so that they are correct on it
- [ ] port `monoidal.Layer.merge`, `Diagram.interchange`, `Diagram.substitute` off `boxes_and_types`
- [ ] port `braided.Diagram.simplify`, `naturality`
- [ ] port `rigid.Diagram.transpose_box`
- [ ] port `tensor.Diagram.grad`
- [ ] port `grammar.pregroup.Diagram.normal_form`
- [ ] port `quantum.tk.to_tk`, `quantum.circuit.Circuit.to_tn`
- [ ] delete `Layer.boxes_and_types`, port its tests and docs
- [ ] `CHANGELOG.md`
