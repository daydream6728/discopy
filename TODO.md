# TODO

## Round 4

> here’s the e hypergraph paper we reinvented in discopy-next, make sure our implementation matches the theory and reproduce their examples

@toumix, in a session, with the paper attached: Tiurin, Barrett, Ghica and Hu, *Equivalence Hypergraphs: DPO
Rewriting for Monoidal E-Graphs*, [arXiv:2406.15882](https://arxiv.org/abs/2406.15882) (v2, May 2025).

The paper's semantics for e-graphs is the free semilattice-enriched Cartesian category: an e-class with several
e-nodes is their join, drawn as an e-box (Fig. 3, Algorithm 1), and composition and tensor distribute over joins
(Fig. 4). Its e-hypergraphs are hierarchical, with nested e-boxes of any arity, so that they represent any
symmetric monoidal theory; an e-graph translates to flat ones, with one output per e-box. This pull request is
that flat, Cartesian case, as round 3 asked, so the boxes are to check it against the paper there and reproduce
the figures.

- [x] `EHypergraph.nodes`: the e-nodes of each class, congruent producers being one, egg's hashcons invariant
      (Definition A.40); `sections` chooses among them, so that it lists each section once
- [x] `EHypergraph.to_diagram`: the translation of Fig. 3 and Algorithm 1, a class of several e-nodes drawn as an
      e-box, the join of its e-nodes; boxes that are not cartesian stay outside, as context
- [x] The law `translation`: distributing the joins of the translation (Fig. 4) gives the sections, modulo the
      naturality of copy and discard, i.e. per class as the paper's copies after an e-box say, not per occurrence
- [WIP] @session_01KNULn8MaXHE4DEmAMcdCz7-2026-10-19 15:58 A notebook reproducing the paper's examples: Fig. 1 rule by rule, Figs. 3 and 25, Figs. 26 and 27, the
      deletion of Fig. 17 and Appendix G, and the cycle the paper leaves out, with tests pinning each
- [WIP] @session_01KNULn8MaXHE4DEmAMcdCz7-2026-10-19 15:58 Say in the module docstring how the implementation reads the paper, and what it leaves to #103: nested
      e-boxes of any arity, the join of Definition VI.1, DPO rewriting over monoidal theories
