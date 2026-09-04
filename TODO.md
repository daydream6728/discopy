# TODO

> I need some help on #658. I want to revise the property testing
> infrastructure by making shapes (ComposablePair, TraceVanishing, etc...) as
> finitely presented categories, and then implementing strategies as functors
> from these shapes to the kleisli category over
> `hypothesis.strategies.SearchStrategy`.
>
> In a new branch on my discopy fork, i want to experiment with a new design
> that reimplements every shape as such and automatically derive an efficient
> search strategy. i know this will create issues with cyclic imports, but
> assuming this causes no issue, planify the ideal interface that it could
> have. take maximal advantage from this categorical architecture.
>
> in an isolated module (call it discopy.shape), define shapes as computads,
> sampling as morphisms in the kleisli category, and search strategy
> derivation as a functor between the two.

- [x] `Sample`, the Kleisli category of `hypothesis.strategies.SearchStrategy`,
  as a concrete `MarkovCategory` in the `python.Function` mold, with `pure`
  embedding deterministic functions; tested on its own.
- [x] `Shape`, a monoidal computad presented in the doctrine's own free
  category, with `Model` as the doctrine's `Functor` out of it — typing the
  box images is the whole validation; models unpack in generator order.
- [x] `Shape.sampling() -> markov.Diagram`, the pure sampling plan, and
  `sampler(carrier): markov.Functor` into `Sample` evaluating it;
  `ComposablePair` end-to-end.
- [x] `Shape.grid(n_rows, n_columns)` deriving `ComposablePair`,
  `ComposableTriple`, `HorizontalPair` and `Bifunctor`; the `active`-row
  padding as a degeneracy applied after sampling.
- [x] The traced, closed and feedback shapes as presentations — words carry
  the constraints, `ev` and identities as derived cells.
- [x] Sorts on generators (`Atomic`, `NonEmpty`, `Small`,
  `BoundaryConnected`, `min_leaves`) as params to the primitive draws.
- [x] Wire `resolve` so `Axiom.strategy` annotations (`ComposablePair[C1]`)
  reach `Shape.__getitem__`; delete the hand-written `strategy()` and
  `__new__` validators as each shape ports.
- [WIP] @e89cefa6-2026-09-04 Equivalence checks: derived strategies find the
  structures the old ones found; the full suite and `proptest/` green;
  CHANGELOG entry.
