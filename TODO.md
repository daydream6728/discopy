> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Rulings: https://github.com/rel-int/discopy-next/issues/31#issuecomment-6349748150

- [x] B76, box reading: each level gets its own `Bubble` and `bubble_factory`, so bubbles compose at every level; `rigid.Bubble` carries `z`, and its rotation turns `dom`, `cod` and `z` and leaves the args alone, so `f.bubble().r != f.r.bubble()`
- [x] B82, mark at frobenius, negate in zx: the dagger of a phased spider keeps its phase and toggles `is_dagger`, so a string phase gets a dagger and `F(s.dagger()) == F(s).dagger()`; `quantum.zx` keeps its own `-phase`
- [ ] B79, `substitute`: `i` is a box index, so a foliated diagram is split into staircases first
