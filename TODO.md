# TODO

> make a plan to ensure that we cover a significant portion of the search space, review all search strategies and investigate blind spots test that we can get boundary disconnected diagrams, disctonnected diagrams, for cmap and hypergraph we should be able to generate non trivial disconnected components, etc... ideally, we should be able to distinguish pure xfails from partially true cases for subspaces. in testing.py, we should be able to define strategies for specific classes of diagrams/cmaps/hypergraphs/etc... and do e.g
> ```py
> axiom_that_almost_holds = BaseClass.axiom_that_almost_holds.weaken(f=BoundaryConnected[C1])
> ```

Phase 8 of the purification: widen the search to the whole carrier and
make every restriction of a law to a subspace explicit.

What the audit of this tree already shows:

- The matrix never leaves the boundary-connected subspace. `Axiom.strategy`
  resolves every `C1` annotation to a bare `factory.strategy()`, whose
  `boundary_connected=True` default is the implicit quantifier of every
  cell; `boundary_connected=False` is exercised by two unit tests only.
- `monoidal.Layer.strategy` accepts `boundary_connected` and never reads
  it; `symmetric.Layer.strategy` forwards it into that void.
- `Hypergraph.strategy` and `CMap.strategy` are images of `from_diagram`:
  no generated hypergraph has an isolated spider, no generated map has a
  loop unless a trace built one, and closed components only arise through
  the diagram path. Whole regions of both representations are dark.
- Fourteen `.failing` declarations xfail whole cells with no way to state
  the subspace on which the law does hold.

The work, laws first per PROPTEST.md:

- [ ] `Axiom.weaken(**subspaces)` in `testing.py`: the same law with the
      named parameters generated from a subspace strategy, `C0`/`C1` in a
      subscript resolving to the carrier the way annotations do. Assigned
      to its own attribute it enrols itself through
      `__set_name__`/`declared_axioms`, so a carrier states
      `law_on_connected = Base.law.weaken(f=BoundaryConnected[C1])` beside
      `law = Base.law.failing(reason)`, and the matrix shows one xfail and
      one green cell instead of one blanket xfail.
- [ ] Subspace strategies in `testing.py` on the `Atomic`/`NonEmpty`
      pattern, validating membership on construction so records replay
      honestly: `BoundaryConnected[T]` first, then the ones the weakened
      cells below need (equal-length swap halves for `finset`, homogeneous
      memory for `feedback`, small dimensions for `Matrix`).
- [ ] Reach: wire up or remove `Layer.strategy`'s dead `boundary_connected`
      parameter; extend `Hypergraph.strategy` and `CMap.strategy` past the
      image of `from_diagram` — isolated and zero-legged spiders for
      hypergraphs, loops for maps, closed components containing at least
      one box for both. Pin each shape in the module's `test_strategy`
      with a bespoke `find`: a boundary-disconnected diagram, a diagram
      with two components, a non-trivial closed component, a map with a
      loop, a hypergraph with an isolated spider.
- [ ] Rarity: tag the connectivity classes with `hypothesis.event` and
      check each is drawn at the matrix budget of 25 examples; rebalance
      the strategy weights where a class is starved.
- [ ] Flip the default: `Diagram.strategy` searches the whole space
      (`boundary_connected=False`), hypergraphs and maps inheriting the
      widening. Triage every cell that goes red: a genuine bug gets a
      record per PROPTEST.md, a law that only holds on a subspace gets
      `.weaken` with the restriction stated in the code — starting with
      the conversion roundtrips, whose `to_diagram` requires boundary
      connectedness by design.
- [ ] Audit the fourteen `.failing` declarations: pure or partially true?
      Candidates for a weakened green sibling: the three `Matrix` copy
      laws (hold below dimension 2), the three `finset` swap laws (an
      inverted swap is correct on equal-length halves), and
      `feedback_joining` (holds on homogeneous memory, #606). The
      free-quotient failures (`braided`, `pivotal`, `ribbon`, `compact`,
      `biclosed`, `cat.Functor.unitality`) are expected pure: their
      reasons should say so.
- [ ] Guardrails green (`pflake8`, unit suite, full matrix), CHANGELOG
      updated, TODO deleted.
