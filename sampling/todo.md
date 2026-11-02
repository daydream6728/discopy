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

- [ ] `str_transparency` on symmetric and compact diagrams is green by
      blind spot (`retrospective.md`): decide between a law up to
      interchange, a transparent `str` for layers of several boxes, or a
      sampler per law (`frobenius.Diagram.str_transparency` already fails
      under `fast`)
- [ ] `str_transparency` on compact diagrams fails on a lone rotated box
      `Box('f', a, a).r` under 1a: the law documents it as off its domain
      but does not assume it away
- [ ] unrelated, also on unchanged code: `pytest --doctest-modules
      discopy/monoidal.py discopy/symmetric.py discopy/hypergraph.py` fails 4
      doctests of `symmetric` with `AxiomError: Expected Wire, got Ty`, while
      `discopy/symmetric.py` alone passes: doctests leak state across modules

## Milestone 2

- [x] 2b `syntactic_admissible`: `Arrow.admissible`, `search(without=...)`
- [x] 2c `syntactic_grammatical`: `discopy/boltzmann.py`, rules instantiated
      at bounded width, Newton iteration for the generating functions,
      bisection for `rho` and for the size; `testable.SIZE`, inf = critical
- [x] 3a for markov (`draw_typed(monogamous=False)`: functions) and compact
      (`draw_typed_bijective`: Brauer)
- [x] `structural_perturbed`: a 3a normal form, then random rewrites
- [x] profile: Hypothesis compiles every `@st.composite` defined per call;
      `search` and `Rule.strategy` are memoised, 2.5 times faster
- [x] distinct draws up to coherence (Weisfeiler-Lehman hash of hypergraphs)

## Milestone 3

- [x] `mutants.py` and a `mutants` experiment; hand-found minima in
      `analysis.md`; the einsum limit (discopy/discopy#447) as the
      historical numeric bug
- [x] semantic sampling: fixed signature, functor into `Tensor`
      (`Matrix[int]` draws its arrays directly, it has no free diagrams)
- [x] convex multi-parameter tuning with `cvxpy` for 2c
- [x] critical sampling: the `boltzmann` experiment at `size=inf`, by
      Hypothesis's choices and exactly from a seed (`grammar_exact`)
- [x] Hypothesis's bias: the `uniforms` experiment
- [x] `analysis.md`, separate from the slides
- [x] `playground.py`: choose a doctrine, a sampler and its parameters, see
      the histograms of what it draws and a gallery of drawings
- [ ] round two doctrines: braided, balanced, traced, rigid, pivotal,
      frobenius, feedback, closed (stubs in `DOCTRINES`)
- [ ] pre-existing, not from this work: `pytest --doctest-modules` on
      `discopy/hypergraph.py` alone fails 4 doctests, on
      `discopy/testable.py` 2, already at d97e2cda3

## Before the full run

- [ ] `--full` budgets are 10 times the quick ones; run the experiments one
      after another on an idle machine, since `throughput` measures speed:
      `uv run --with cvxpy python sampling/experiments.py --full`
- [ ] the hand-found minima in `analysis.md` assume the quick results; check
      the shrunk sizes again after the full run

## After the experiments

- [ ] choose the default sampler of each data structure from the results
- [ ] `Axiom.examples`: counterexamples as regression tests run once per cell
      with `@example` (proposal only)
