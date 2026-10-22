> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

- [x] B85 of #31: `frame_dual_rail` runs on every `draw()` and is not idempotent; `Drawing.then`/`tensor` return the other operand by identity; `draw(show=False)` without a path leaks one pyplot figure per call
- [x] B37 (fable README claim table): `draw()` mutates the drawing it draws
- [ ] B83 of #31, colour part: `Matplotlib.draw_spiders` and every TikZ path index `COLORS[color]` bare; a coloured twist fills its back with `f"dark_{color}"`
- [x] B87 of #31, drawing part: `test/drawing/drawing.py` mutates the global `H` gate and never restores it (already fixed on `main` by f862f4ca, #99)
- [ ] CHANGELOG entries under `### Fixed`
