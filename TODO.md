> Let's finish the discopy-next bootstrap e.g. the wip from this PR should be merged in next and closed upstream https://github.com/discopy/discopy/pull/677/changes
> same for the ZX experiments: they become a single notebook in next

The "ZX experiments" are discopy/discopy#626 (reproduction of Stoltz & Vilmart, arXiv:2608.14872, and its generalisation) and discopy/discopy#688 (an independent minimality analysis of Vilmart 2019), two proofs of one result: they become one notebook here.

- [x] one marimo notebook `docs/notebooks/zx-minimality.md` merging #626 and #688, research-log scaffolding dropped, both proofs kept where they differ
- [x] the exact symbolic checker of #688 folded into notebook cells
- [x] every numeric claim re-checked under next's ZX conventions (phases in turns, `zx.Diagram.eval` the standard interpretation)
- [x] `docs/index.rst` toctree and one `CHANGELOG.md` entry citing both upstream pull requests
- [x] `python docs/export_notebooks.py --check zx-minimality` passes
