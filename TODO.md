# TODO

> what if functors could map not just diagrams but any concrete
> category? in this case, could to_diagram, to_hypergraph and to_map
> be functors and inherit all the axioms on Functor? what if we make
> an Equivalence(Functor, DaggerCategory) class which would be a
> functor with an inverse, i.e. F >> F.dagger() == Id() == F.dagger
> >> F

> run the equivalence round

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-23 17:20 Probe the
      mechanics: how a level's `Functor` binds its `dom`, how the
      functor laws spell their premises, what the `Serialisable` laws
      make of a functor with no mappings
- [ ] `cat.Equivalence`, a functor with an inverse: `decode` and
      `dagger`, the pointwise laws `section` and `retract` (functor
      equality being #648, `F >> F.dagger() == Id()` is quantified
      over the arrows), `composition` and `identity` preservation,
      and the functor-category laws declared inapplicable on a
      single functor
- [ ] `monoidal.Diagram.ToHypergraph` and
      `symmetric.Diagram.ToMap`, generators wrapping the conversion
      methods, every level getting its own by the `Generator`
      diamond so the classifications inherit like the diagrams do
- [ ] Migrate `hypergraph_section`, `map_section` and `map_retract`
      with their per-level classifications from the diagram classes
      onto the equivalences, keeping agreement, staircases,
      rewriting and drawing where they are
- [ ] Run every cell at every level, classify what the runs show,
      tests for the new classes
- [ ] `ty check`, `ruff check`, pytest, proptest fast + targeted
      cells, CHANGELOG, close
