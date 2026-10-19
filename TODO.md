# TODO

> go ahead with the port rows

(daydream6728, 2026-10-19, interactive, ruling on the triage of #132, which quotes the bootstrap prompt verbatim: *"Port the rows that don't merge, one discopy-next PR each, carrying over the upstream description."*)

The **port** row discopy/discopy#794: the tensor and matrix categories round-trip through JSON. Ported as a merge commit of its upstream head, so its commits survive, with the conflicts resolved against next.

- [ ] measure which of its four defects reproduce on next `main`: the trees of `Dim` and `Nat` are fixed here already, the dtype name and `Matrix.to_tree` are not
- [ ] merge discopy/discopy#794, its `from_name` folded into next's `resolve_factory` rather than kept beside it
- [ ] `Matrix` declares `serialisation` applicable now that it has a tree
- [ ] `CHANGELOG.md` by hand
- [ ] pflake8, pylint (`fail-under`) and pytest on the merged tree
