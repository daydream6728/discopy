> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

USER's ruling on #161, live (10-22), via buttons:

> Fix after #268

recorded on the issue as https://github.com/rel-int/discopy-next/issues/161#issuecomment-6349441015:

> USER ruled live (10-22): fix as a bug. A layer maps by one n-ary tensor of its whiskered images when the codomain is an `abc.MonoidalCategory`, and by the `@` fold otherwise (the kleisli channels). A prototype measured ~40x faster at 200 boxes, with reprs and SVGs identical. It lands after #268, which is in `monoidal.py` today. `Drawing.tensor` stays a fold, as a follow-up.

#268 is merged.

- [ ] #161: `monoidal.Functor` maps a `Layer` by one n-ary `tensor` of its whiskered images when `cod.ar` is an `abc.MonoidalCategory`, by the `@` fold otherwise
- [ ] every `abc.MonoidalCategory` in the package takes `tensor(*others)`, so the n-ary path never hits a binary one
- [ ] `symmetric.Permutation.__rmatmul__`: the n-ary image equals the fold's on layers with permutations next to boxes
- [ ] every SVG baseline stays byte-identical
- [ ] tests: the n-ary path is taken (one `tensor` call per layer), the kleisli fallback still folds
- [ ] `CHANGELOG.md`: one bullet at the end of `### Performance`
