# Sampling experiments: todo

Context for whoever picks this up, e.g. a cloud session running `--full`.
Not a mutex: just the state of the work. The design was settled in a grilling
session with the human; the decisions are below, the explanations in
`presentation.md`.

## Decisions

- Each sampler is a method `strategy_<sampler>` on the classes where it makes
  sense; `Arrow.strategy` calls the one named by the class attribute
  `sampler`; `PROPTEST_SAMPLER=<sampler>` sets it for the whole matrix
  (`proptest/conftest.py`). Defaults are unchanged: `syntactic_baseline`,
  and `mixed` (2a or 3b, half each) for symmetric diagrams.
- Every experiment runs one sampler at a time. Each data structure keeps its
  own signature: no shared signature across samplers.
- Main regime is critical (heavy-tailed) sampling, `explore` should use it;
  size-matched runs are a control. Distinct draws matter more than size.
- Planted bugs are monkeypatches in `sampling/mutants.py`, one per sampler
  that it hardly finds and another sampler finds: mathematically meaningful
  for categorical laws (normal-form assumptions, coherence, e.g. Selinger's
  interlocked traces for hypergraph/cmap samplers), classic programming bugs
  for concrete ones (removed edge cases, off-by-one, `<` vs `<=`, parsing
  ambiguity). Smallest counterexamples are found by hand, no automation.
- Real bugs found go to `retrospective.md`, fixed when simple.
- `cvxpy` is fine as a dependency of the experiments.
- Work locally: commit, never push.

## Milestone 1

- [x] dispatch: `Arrow.sampler`, `strategy_<sampler>`, `PROPTEST_SAMPLER`
- [x] 1a `representational_baseline`, 1b `representational_goal_directed`
      on `monoidal.Diagram`, with permutations on `symmetric.Diagram`
- [x] 2a `syntactic_baseline` (the existing `search`)
- [x] 3a `structural_typed` (`Hypergraph.draw_typed`), 3b
      `structural_implicit` (the existing quotient strategy)
- [x] `experiments.py`: `throughput`, `matrix` under `--quick`
- [x] `presentation.md`, `retrospective.md`

## Found on the way

- [ ] `str_transparency` on symmetric diagrams is green by blind spot
      (`retrospective.md`): decide between a law up to interchange, a
      transparent `str` for layers of several boxes, or a sampler per law
      (`frobenius.Diagram.str_transparency` already fails under `fast`)
- [ ] unrelated, also on unchanged code: `pytest --doctest-modules
      discopy/monoidal.py discopy/symmetric.py discopy/hypergraph.py` fails 4
      doctests of `symmetric` with `AxiomError: Expected Wire, got Ty`, while
      `discopy/symmetric.py` alone passes: doctests leak state across modules

## Milestone 2

- [ ] 2b `syntactic_admissible`: mark admissible rules, sample without them
- [ ] 2c `syntactic_grammatical`: bound the width, instantiate the rules as a
      grammar, Boltzmann sampler with numpy bisection tuning
- [ ] 3a for markov (non-monogamous: functions) and compact (Brauer)
- [ ] `structural_perturbed`: normal form, then random rewrites in context;
      pairs of equal diagrams for `to_hypergraph`, `normal_form`, `==`
- [ ] profile why every sampler is under 100 diagrams per second
- [ ] distinct draws up to coherence, not only up to box names

## Milestone 3

- [ ] `mutants.py` and a `mutants` experiment: kill rate per sampler,
      shrunk size against a hand-found minimum; mention the einsum
      52-index limit (discopy/discopy#447) as the historical numeric bug
- [ ] semantic sampling: fixed signature, functor into `Matrix[int]`;
      support table sampler × semantic category
- [ ] convex multi-parameter tuning with `cvxpy`, beyond 2c if possible
- [ ] critical sampling: size histograms, overruns, distinct draws
- [ ] round two doctrines: braided, balanced, traced, rigid, pivotal,
      frobenius, feedback, closed (stubs in `DOCTRINES`)

## After the experiments

- [ ] choose the default sampler of each data structure from the results
- [ ] `Axiom.examples`: counterexamples as regression tests run once per cell
      with `@example` (proposal only)
- [ ] `--full` run in the background
