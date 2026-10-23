> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Four drawing bugs found while fixing #31, each reproduced on `main` and needing no ruling:

- [x] T08: `Drawing.permutation([1, 0], [X @ Y, Z])` raises: it permutes wires, where `permutation(xs, doms)` permutes blocks at every other level
- [x] T19: a twist in an xcolor-only colour (e.g. `RoyalPurple`) raises `ValueError` in TikZ, where a box in that colour draws
- [x] T20: `Drawing.then(draw_step_by_step=True)` returns a drawing, not a list of steps, when a side is a short identity
- [ ] T21: `use_tikzstyles=True` with a hexcode names the style `#336699_box`, and `#` is TeX's parameter character
- [ ] `CHANGELOG.md`: one bullet for the PR
