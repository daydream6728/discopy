> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Four rulings of USER's, one commit each:

- [x] B88: `Layer(f) >> Layer(g)` raises, saying to compose diagrams, not layers ([ruling](https://github.com/rel-int/discopy-next/issues/31#issuecomment-6351016378))
- [ ] B88: a structural box has `time_step` `None`, not 0 ([ruling](https://github.com/rel-int/discopy-next/issues/31#issuecomment-6351077357))
- [ ] #168: a `finset.Permutation` reprs with its class, its `str` stays the tuple ([ruling](https://github.com/rel-int/discopy-next/issues/168#issuecomment-6351077988))
- [ ] #262's nan: a `tensor.Box` holding nan equals itself ([ruling](https://github.com/rel-int/discopy-next/issues/31#issuecomment-6351077357))
- [ ] `CHANGELOG.md`: one bullet for the PR
