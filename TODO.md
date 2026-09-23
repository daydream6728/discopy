# TODO

> in discopy/discopy:refactor/serde, we managed to eliminate the
> test_eval_repr or whatever it was called, by absorbing it into the
> axioms. i want to do the same for conversion, normal_form and
> drawing, and instead just have everything as axioms checked in
> test_axioms.py. how would you do it?

> do it, but drop every *_typing axiom and don't do equations over
> tuples like you tried to do on permutation_swaps. forget about
> Permuted, just port the axioms that make sense and possibly create
> new ones, based on the literal categorical definitions

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-23 15:10 Probe the
      open questions: the quotient of each level's `Equation`, whether
      `to_drawing` is functorial and rendering deterministic on the
      nose, what `abc` already states about permutations
- [ ] State the conversion laws on `monoidal.Diagram` as
      single-equation axioms: `hypergraph_section`, `map_section`,
      `map_hypergraph_agreement`, `staircase_encoding`
- [ ] State the rewriting laws: `normal_form` and `foliation` as
      idempotent representatives, weakened to the boundary-connected
      subspace where their decision procedure asks for it
- [ ] State the drawing laws from the literal definitions that hold,
      folding the render smoke test into a law's body
- [ ] Sweep the classifications: every level list and xfail mark of
      the three suites becomes `.inapplicable`, `.failing` or
      `.weaken` on the level it concerns, re-declared across diamonds
- [ ] Delete `proptest/test_conversion.py`, `test_normal_form.py` and
      `test_drawing.py`, moving what their conftest needs
- [ ] `ty check`, `ruff check`, pytest, proptest fast + targeted
      cells, CHANGELOG, close
