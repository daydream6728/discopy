> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

- [x] #169 slice 1 (ruling https://github.com/rel-int/discopy-next/issues/169#issuecomment-6349666772): a field tuple and one keyword-only `rebuild(**changes)` on `cat.Box`, called by `dagger`, `rotate`, `subs` and `lambdify`; one tuple per `Box` subclass whose constructor takes other fields; the conformance test over every `Box` subclass
- [x] `tensor.Bubble` keeps its `func` through `dagger`, and its `repr` and `==` read `func` and `is_dagger`
- [ ] CHANGELOG.md, one bullet
