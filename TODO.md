# TODO

> go ahead with the port rows

(daydream6728, 2026-10-19, interactive, ruling on the triage of #132, which quotes the bootstrap prompt verbatim: *"Port the rows that don't merge, one discopy-next PR each, carrying over the upstream description."*)

The **port** row discopy/discopy#763: every `then` takes `(self, *others)`. Ported as a merge commit of its upstream head, so its commits survive, with the conflicts resolved against next.

- [ ] merge discopy/discopy#763, keeping next's n-ary `Tensor.then` and `Channel.then` (#60)
- [ ] `CHANGELOG.md` by hand
- [ ] pflake8, pylint (`fail-under`) and pytest on the merged tree
