# TODO

> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

USER's live rulings of 10-22, as relayed on the issues:

> USER ruled live (10-22): **weaken the law** rather than print every entry. `Matrix`/`Tensor` keep their readable repr. `transparency` is declared on them only up to `config.NUMPY_THRESHOLD` entries and compared with `allclose`. STYLE.md's "always" gets that caveat for arrays. #143 closes as a duplicate when this lands.

([#156 (comment)](https://github.com/rel-int/discopy-next/issues/156#issuecomment-6349550631))

> USER ruled live (10-22): **uniform**. An uncoloured `monoidal.Wire` prints as `monoidal.Wire('x')`, like every other level's wire, and `monoidal.Ty('x')` prints `monoidal.Ty(monoidal.Wire('x'))`. This drops the "Ty keeps printing as now" clause of the proposal above. Old printed text still evaluates.

([#140 (comment)](https://github.com/rel-int/discopy-next/issues/140#issuecomment-6349551782))

- [x] #156: `transparency` on `Matrix` and `Tensor` weakened to arrays of at most `config.NUMPY_THRESHOLD` entries, with a test
- [x] #156: STYLE.md's transparency paragraph says arrays read back up to elision and rounding
- [x] #140: an uncoloured `monoidal.Wire` reprs as `monoidal.Wire('x')`, pinned expectations updated
- [x] CHANGELOG `### Changed`, at the end
- [ ] merge `origin/main` once #268 lands, full suite, pflake8, pylint, proptest cells of `matrix`
