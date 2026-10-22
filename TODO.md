> For a stronger stress case: implement the rewrite rules of the ZX calculus as hypergraph diagrams with a single box for Hadamard and try to beat the performance of the pyzx library.

(USER, live, 2026-10-22, on top of rel-int/discopy-next#224, double-pushout rewriting.)

Rewriting a hypergraph with `Hypergraph.rewrite` rebuilds the whole host at each step: 0.25 s for a
host of pyzx's size, against 3 s for pyzx's whole `full_reduce`. A left-linear rule has one pushout
complement, the host minus the image of its left side less the boundary (Bonchi et al. I, Prop.
3.18; II, Prop. 24 for the boundary complement), so a step can be done in place in the size of the
rule. This branch is that engine; the ZX rules are the next one, stacked on it.

- [x] `Rewriter`: boxes and spiders by id, `substitute`, `merge`, `glues`, `matches`, `normalize`,
  `to_hypergraph`, the match search shared with `Hypergraph`
- [x] differential test against `Hypergraph.rewrite` on random frobenius and symmetric hosts
- [x] `Hypergraph(..., _scan=False)` skips the checks, as `cat.Arrow` does
- [x] relabel the nested wires directly in `Hypergraph.__init__`
- [ ] `pflake8`, `pylint`, `coverage run -m pytest --skip-extra`
