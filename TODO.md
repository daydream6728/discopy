# TODO

> go ahead with the port rows

(daydream6728, 2026-10-19, interactive, ruling on the triage of #132, which quotes the bootstrap prompt verbatim: *"Port the rows that don't merge, one discopy-next PR each, carrying over the upstream description."*)

The **port** row discopy/discopy#761 through discopy/discopy#807, which resolves upstream `main` into it: every `tensor` takes `(self, *others)`, `n`-ary where the fold costs. Ported as a merge commit of #807's head, so the commits of both survive, with the conflicts resolved against next.

- [ ] merge discopy/discopy#807, keeping next's dtype promotion (#733) in the `n`-ary `Matrix.tensor` and `Tensor.tensor`, and next's `Channel.dims`
- [ ] a test that the `n`-ary tensor promotes, which neither side has
- [ ] `CHANGELOG.md` by hand
- [ ] pflake8, pylint (`fail-under`) and pytest on the merged tree
