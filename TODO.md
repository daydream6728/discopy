> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

B81 of #31, parts (a) and (d), which need no ruling:

- [x] (a) `FC`, `BC`, `FX`, `BX` are boxes: `BinaryTerm` is built the way `TypeRaising` is, each subclass passing its `cod` up, with no new public names, so that a binary term composes, tensors and draws
- [x] (d) a nested `cfg.Tree` has a `dom`, the tensor of its branches' doms, so that it can be applied
- [ ] `CHANGELOG.md`, one bullet
