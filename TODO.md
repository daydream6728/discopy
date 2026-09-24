# TODO

> this ONE_FUNCTOR stuff sucks, we shouldn't define functors as
> subclasses of Functor, but by instances of Functor

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-24 Make
      `cat.Equivalence` a class of instances: a pair of callables
      `encode` and `decode` between ``dom`` and ``cod``, `dagger`
      swapping them, equality and hash on the fields — delete
      `Inverse`, `ONE_FUNCTOR` and its six marks, `__reduce__` and
      the subclass-only strategy
- [ ] Replace the `ToHypergraph` and `ToMap` subclass towers by
      `Diagram.hypergraph_equivalence` and
      `Diagram.map_equivalence` classmethods building the instance
      of each level
- [ ] Move the equivalence laws back onto the diagram classes —
      `hypergraph_section`, `hypergraph_retract`,
      `hypergraph_composition`, `hypergraph_identity` on
      `monoidal.Diagram`, `map_section`, `map_retract`,
      `map_composition`, `map_identity` on `symmetric.Diagram` —
      with the classifications where they break: braided, traced,
      rigid, pivotal, closed
- [ ] Delete the per-level subclasses, the `ClassVar` annotations,
      the autosummary entries and the module exports
- [ ] `ruff check`, `ty check`, pytest, fast + dev cells of the
      moved laws, CHANGELOG, close
