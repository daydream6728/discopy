> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

- [x] #16: `biclosed.Ty`'s atoms are `biclosed.Wire`, and a plain `cat.Ob` or a transparent `monoidal.Wire` read back from a dump, a pickle or printed text is upgraded to one
- [x] `x ** y` in biclosed is `x << y` (ruling https://github.com/rel-int/discopy-next/issues/31#issuecomment-6351016378): a `biclosed.Exp` read back or built by hand gives `Over`, `exp_factory` dropped where nothing reads it
- [x] A term inside a diagram is drawn as one box labelled with its `str` (same ruling), `t.draw()` alone keeps drawing `t.eval()`
