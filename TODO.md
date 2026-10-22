# TODO

> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

USER's live ruling of 10-22, as relayed on the issue:

> USER ruled live (10-22): **state it now**. The convention: each generator is bound to itself by its name. Terms whose generators have clashing or non-identifier names lie outside the law's domain. `str_transparency` sits next to `transparency` on `Testable`.

([#163 (comment)](https://github.com/rel-int/discopy-next/issues/163#issuecomment-6349551175))

- [x] #163: `Testable.str_environment`, the environment with each generator of a term bound to itself by its name, walked per level: types, boxes, exponentials, sums, bubbles, terms
- [x] #163: `Testable.str_transparency` beside `transparency`, clashing or non-identifier names assumed away
- [x] #163: strategy boxes named by identifiers, so that the cells check something
- [x] #163: carriers that break the law for a real reason declared `.failing`, reported as new bugs: no carrier of the matrix breaks it; `Hypergraph` is not `Testable` and `abc.Nat` no cell, both reported
- [x] CHANGELOG `### Added`, at the end
- [x] full suite, pflake8, pylint, the whole property matrix
