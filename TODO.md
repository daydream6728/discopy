# TODO

> I need some help on #658. I want to revise the property testing
> infrastructure by making shapes (ComposablePair, TraceVanishing, etc...) as
> finitely presented categories, and then implementing strategies as functors
> from these shapes to the kleisli category over
> `hypothesis.strategies.SearchStrategy`.
>
> In a new branch on my discopy fork, i want to experiment with a new design
> that reimplements every search strategy as such. i know this will create
> issues with cyclic imports, but assuming this causes no issue, planify the
> ideal interface that it could have. take maximal advantage from this
> categorical architecture and propose a plan with examples of how it would
> look like to define shapes and axioms.

- [x] Survey the baseline: fetch upstream discopy/discopy#658 and read
  `discopy/testing.py`, the axioms on `discopy/abc.py` and the `proptest/`
  matrix.
- [x] Write `PLAN.md`: the mathematical picture, the ideal interface, worked
  examples of shapes and axioms at every level of the hierarchy, what the
  design deletes, and the staged implementation plan.
- [ ] Stage 0 — merge upstream discopy/discopy#658 into this branch as the
  baseline to refactor.
- [ ] Stage 1 — `Search`, the Kleisli category of the `SearchStrategy` monad,
  as a Markov category with tests of its own.
- [ ] Stage 2 — `Term`, the syntax relations are stated in, with `Term.eval`
  by structural recursion through an instance functor.
- [ ] Stage 3 — `Presentation` and the generic `instances`; port the
  `cat`-level axioms and retire their bespoke argument shapes.
- [ ] Stage 4 — port the monoidal, symmetric, traced, closed and feedback
  shapes; delete `PastingDiagram` and every `Trace*`/`Feedback*`/`*Currying`
  strategy class.
- [ ] Stage 5 — subspaces as generation constraints, counterexample records
  as functors, docs, and the strategy-reach audits.
