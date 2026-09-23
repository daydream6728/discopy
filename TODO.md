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

- [x] Probe the open questions: the quotient of each level's
      `Equation`, whether `to_drawing` is functorial and rendering
      deterministic on the nose, what `abc` already states about
      permutations
- [x] State the conversion laws on `monoidal.Diagram` as
      single-equation axioms: `hypergraph_section`, `map_section`,
      `map_hypergraph_agreement`, `staircase_encoding`
- [x] State the rewriting laws: `normal_form` and `foliation` as
      idempotent representatives, weakened to the boundary-connected
      subspace where their decision procedure asks for it
- [x] State the drawing laws from the literal definitions that hold,
      folding the render smoke test into a law's body
- [x] Sweep the classifications: run every new cell at every level,
      then declare `.inapplicable`, `.failing` or `.weaken` on the
      level each observed failure concerns, re-declared across diamonds
- [x] Express the subspaces: `Diagram.strategy` takes named subspaces
      for `Axiom.weaken` to quantify over, and `map_retract` states the
      equivalence up to the level's own quotient, which is spacial like
      the map, where the syntactic comparison is falsified
- [x] Delete `proptest/test_conversion.py`, `test_normal_form.py` and
      `test_drawing.py`, moving what their conftest needs
- [ ] `ty check`, `ruff check`, pytest, proptest fast + targeted
      cells, CHANGELOG, close
