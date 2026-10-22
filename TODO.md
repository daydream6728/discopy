> For a stronger stress case: implement the rewrite rules of the ZX calculus as hypergraph diagrams with a single box for Hadamard and try to beat the performance of the pyzx library.

(USER, live, 2026-10-22, on top of rel-int/discopy-next#224, double-pushout rewriting, and #288,
the in-place `Rewriter`. Asked how: `full_reduce`, with a normal form no larger than pyzx's in
spiders, Hadamard edges and T-count, raced on wall-clock time; the rules that are schemas, local
complementation and pivoting, instantiated for each match.)

A graph-like ZX diagram is a hypergraph over `zx.Diagram`: green spiders are its spiders, so fusion
is the pushout itself, a Hadamard edge is the box `zx.H`, a phase is the effect `Z(1, 0, phase)`
and a red spider is a green one with `H` on each leg. Each step of pyzx's `full_reduce` is a pair
of hypergraphs built for its match, left-linear, so that the `Rewriter` applies it in place, and a
sound ZX equation on its own.

- [x] `quantum.graphlike`: `Simplifier`, a `Rewriter` that indexes Hadamard edges, loops and phases
- [x] the rules: spider fusion and phases, identity removal, local complementation, pivoting
  (inner, along a boundary, along a gadget), gadget fusion, each a sound ZX equation
- [x] `full_reduce` with pyzx's rule priorities and a min-degree agenda; `from_diagram`,
  `from_pyzx`, `to_pyzx`, `size`
- [x] tests: every step checked a homomorphism that glues and a ZX equation on 24 random circuits;
  the normal form against pyzx's (T-count equal, spiders within one)
- [x] `benchmark/test_zx.py`, graphlike against pyzx on the same random circuits
- [x] docs: module summary, API page, bibliography, `CHANGELOG.md`
- [x] `pflake8`, `pylint` (`fail-under` 9.06), `pytest --skip-extra`
- [x] copy and supplementarity, the two rules pyzx 0.10.7's `full_reduce` adds, which the lock
  pins: the earlier numbers were against 0.7.3
- [ ] beat pyzx 0.10.7: 0.3–0.7× its time from 20 qubits up, but 1.3–1.5× at 10 qubits × 500
  gates
