# Changelog

All notable changes to DisCoPy are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Changes since [`1.2.2`](https://github.com/discopy/discopy/releases/tag/1.2.2).

### Added

- A counterexample ledger and a property-first protocol: `PROPTEST.md`
  instructs agents to state laws before implementing, to record every
  counterexample found against a law in
  `proptest/test_counterexamples.py` — the bound axiom and the arguments
  the search shrunk the failure to, replayed deterministically on every
  run and xfailed while the axiom is declared `.failing` — and to audit
  the search strategy whenever a bug escapes it, by checking reach,
  rarity and observation in turn. This supersedes `Axiom.falsify` as the
  debugging entry point, which remains for interactive exploration.
- Ad-hoc property tests beside the axiom matrix, checking boolean
  properties rather than structured equations, over the same carriers and
  strategies: `proptest/test_conversion.py` checks that `to_diagram` is a
  section of `to_hypergraph` and `to_map` preserving boundaries, and that
  encoding through a map or directly gives the same hypergraph — except
  for `markov`, `closed` and `frobenius`, whose copies and spiders only
  the hypergraph encodes as spiders; `proptest/test_repr.py` checks
  `eval(repr(x)) == x` in a fresh environment loading `from discopy
  import *`; `proptest/test_pickle.py` checks that pickling roundtrips
  every carrier, preserving its class. Decoding a trace, cup or cap can
  need swaps that `traced`, `balanced` and `pivotal` do not have, and an
  uncoloured `monoidal.Wire` reprs as the `cat.Ob` that `Ty` coerces:
  those cells are expected failures.
- The dagger laws join the axiom matrix: `dagger_involution` and
  `dagger_contravariance` on `abc.Category`, `dagger_monoidality` on
  `abc.MonoidalCategory`. `monoidal.Diagram` checks monoidality modulo
  `normal_form` — the premonoidal tensor biases the two sides by an
  interchange — `symmetric.Diagram` restores the plain law, checked up to
  hypergraph like the rest of its equations, and `cmap.CMap` checks it up
  to the hypergraph the map encodes, since the dagger reverses the order
  the boxes are stored in. The laws are inapplicable where there is no
  dagger: functors, `python.finset.Function` (its `Permutation` restores
  them), `rigid.Ty` and `rigid.Diagram` (`pivotal` restores them) and
  feedback categories, whose delay is not reversible. An `eval(str(x))`
  transparency property was considered and dropped: the strategies draw
  box names that are not Python identifiers, so the equality is not
  statable on generated diagrams.
- The property matrix searches the whole carrier by default, and a law
  that only holds on a subspace says so: `Diagram.strategy`,
  `Hypergraph.strategy` and `CMap.strategy` default to
  `boundary_connected=False`, hypergraphs now reach isolated spiders and
  maps reach loops beyond the image of `from_diagram`, and the
  connectivity classes are tagged with `hypothesis.event` — at the
  matrix budget of 25 examples, over half the draws carry closed
  components. `Axiom.weaken(**subspaces)` states a law's restriction:
  each named parameter is generated from a subspace wrapper that
  validates membership on construction — `BoundaryConnected`, `Small`
  and `HomogeneousMemory` in `discopy.testing` — and is unwrapped before
  the body. The laws checked modulo `normal_form`, which is only defined
  on connected diagrams, are weakened accordingly, and the audit of the
  broken declarations records its verdicts: `Matrix` gains
  `copy_cocommutativity_small` and `copy_counitality_small`, green below
  dimension two, while `copy_monoidal_coherence` reaches dimension two
  from atomic arguments, the `finset` swap laws would need a joint
  equal-halves constraint that per-argument generation cannot state, and
  `feedback_joining` is falsified even on homogeneous memory. The dead
  `boundary_connected` parameter of `Layer.strategy` is removed.
- The quantum carriers join the property matrix, pure Python only:
  `quantum.circuit.Circuit` with a wire strategy of bits, qubits and
  small qudits and the standard gates added to the box distribution, and
  `quantum.zx.Diagram` with Z and X spiders, the Hadamard and swaps over
  `PRO` — which gains the strategy whose absence kept it out, and joins
  the matrix itself, its `identity_typing` inapplicable since a PRO is
  monochrome. The laws that a circuit realises physically are declared
  inapplicable with their reasons: no cloning for the copy family, and
  cups, caps and traces that are Bell preparations and effects — like
  the Z and X spiders of ZX — equal to wiring only up to evaluation.
  Complex gate data does not serialise to JSON, an expected failure.
- The python carriers join the property matrix:
  `python.multiplicative.Function` as a closed symmetric Markov semantic
  carrier and `python.additive.Function` as a symmetric one, both over
  the one-type universe `int` — a shared `python.function.Types` object
  with a strategy of integer tuples, output-selection functions for the
  multiplicative strategy and `finset`-style tag relabellings for the
  additive one. A closure has no useful equality, so each carrier's
  `equation_factory` compares extensionally, probing both sides on
  canonical arguments — recursing through the exponentials with
  canonical callables, so the currying laws are checked semantically.
  The dagger laws are inapplicable (only an additive swap has a dagger),
  a closure neither reprs nor pickles (expected failures), and
  `additive.Function` gains the `@factory` it was missing, without which
  its `ar` resolved to the base class of all python functions.
- The tensor carriers join the property matrix: `frobenius.Dim` with a
  strategy of small dimensions, `tensor.Diagram` whose inherited
  frobenius strategy reaches its spiders, cups and caps out of the box,
  and `Tensor[int]` with a `Matrix`-style strategy over `Dim` boundaries.
  `Tensor` restores the three copy laws that `Matrix` declares broken
  (#606): its copy is a correct spider. The one expected failure is
  transparency — a tensor with more than `config.NUMPY_THRESHOLD` entries
  elides its array as a literal ellipsis, so `eval(repr(x))` cannot
  rebuild it.
- A drawing smoke property, `proptest/test_drawing.py`: for every diagram
  carrier of the matrix, `to_drawing` preserves the boundary and both
  backends render a generated diagram without a baseline — Matplotlib on
  Agg into an in-memory buffer, TikZ into a throwaway file. No images are
  compared: the committed documentation baselines remain the pixel tests,
  this checks that layout and rendering never crash on the diagrams the
  strategies reach — swaps, braids, cups, caps, spiders, bubbles and
  traces included.
- Four more ad-hoc properties: `proptest/test_serialisation.py` decodes
  every carrier back from its tree and its JSON; `proptest/test_eq_hash.py`
  checks that whiskering by the unit is invisible to `==`, `hash` and
  dictionary lookups; `proptest/test_normal_form.py` checks that
  `normal_form` and `foliation` are idempotent and preserve the diagram up
  to hypergraph — expected failure on `rigid`, whose left-handed cups and
  caps `to_hypergraph` rejects; and `test_conversion.py` gains
  `decode(*encode())` up to staircases and the permutation laws, inverse
  by dagger and encoding by swaps.
- An axiom is stated either of a carrier or of one of its elements: a body
  taking `cls` is a law of the category, one taking `self` a law of an
  element, whose receiver the property matrix generates like any other
  argument. Functors are the first such elements, generated by
  `Functor.strategy` as relabellings of the generators — total, so they
  apply to any diagram, and comparable, so the axioms of `Cat` itself can be
  checked on them, which a closure would not be. Each level of `Functor`
  states the preservation of its structure as a law named after the level:
  `monoidal.Functor.monoidal` for the tensor, `braided` for the braid,
  `balanced` for the twist, `symmetric` for the swap, `rigid_cups` and
  `rigid_caps` for the two rigid laws, `markov` for the copy and
  `frobenius` for the spiders, so `frobenius.Functor` inherits all eight.
  Naming a law after the level rather than the operation keeps it from
  shadowing the operation itself, the way every axiom of a diagram carrier
  is named after the law — `PivotalCategory.pivotality` states the equality
  of the two transposes without taking the name of
  `RigidCategory.transpose`. Preservation of identities and of composition
  is not stated separately: a functor is an arrow of `Cat`, so those are
  `Category`'s own axioms, inherited. The equation lives in `self.cod`
  rather than in the carrier, which is what the `eq` parameter could not
  express. `braided` and `balanced` are declared unchecked: the braid of a
  composite type is a chosen sequence of crossings that a functor
  rebrackets, so they hold only up to the braid relations that free
  diagrams do not quotient by.
- Every `Functor` subclass is its own `factory`, which only `cat.Functor`
  declared, so `Functor.ar` resolved to `cat.Functor` at every level.
- `Category`'s own axioms are checked on `Functor`, which is how a functor
  preserving identities and composition is stated: `Functor.ob` is
  `abc.Category` rather than `type[Category]`, so the objects of `Cat` have
  an equation factory, and `identity_typing` is restated of the one category
  a carrier maps, since the matrix does not generate categories. `unitality`
  is declared broken: `MappingOrCallable.then` composes by iterating the keys
  of the left-hand map and the identity functor enumerates none, so `id >> f`
  forgets everything `f` does instead of being `f`.
- The names a free category draws its generators from are one shared
  `testing.GENERATORS` rather than a `tuple("abcde")` repeated in `cat`,
  `monoidal`, `feedback` and `rigid`.
- Concrete semantic carriers in the property matrix: `Matrix[int]` is a
  Markov category and `python.finset.Function` a symmetric one, both with
  their own Hypothesis strategy, so the copy comonoid and the symmetry are
  checked against a semantics rather than against free diagrams only. The
  laws they break are declared `"bug"`: `Function.swap` returns the inverse
  permutation, and `Matrix.copy(x, n)` is wrong for `x, n >= 2`
  ([#606](https://github.com/discopy/discopy/issues/606)).
- Two axioms: `RigidCategory.rotate_contravariance`, i.e. rotation reverses
  composition, and `HypergraphCategory.spider_fusion`, i.e. two spiders
  connected by one leg fuse into one.
- Axiom statuses now record the representation-level equality available to
  combinatorial maps, and diagram/map strategies can generate closed
  components on request. A `"strict"` axiom is checked on the nose, while a
  `"setoid"` one is checked up to the category's `equation_factory`, i.e. up
  to hypergraph from symmetric categories on.
- Declarative categorical axioms, validating argument shapes, and canonical
  Hypothesis strategies following the categorical class hierarchy. A dedicated
  workflow runs the property tests on `main`, manually, and on labelled PRs.
- `Diagram.to_compact` and `CMap.to_compact`, bending curry bubbles into
  coevaluation and feedback. Since a biclosed category has no trace, the
  `biclosed` method lands in `CMap`, which is compact whatever hosts it,
  while the `closed` one stays in diagrams. Unlike `rigid.to_rigid` and
  `interaction.Int`, this keeps the exponential atomic and bends the wire
  with `biclosed.Coeval`, the transpose of `Eval`, which a biclosed
  category only has when its exponential is read at a reflexive object
  ([#532](https://github.com/discopy/discopy/pull/532)).
- A style review workflow: when a same-repo pull request leaves draft or
  gets the `style-review` label, one model request reads every changed
  Python file whole — with the package-local files they import as context —
  checks the diff against the file's own conventions and `STYLE.md`, and
  discopy-bot posts the findings as one review — style only, correctness
  stays with the correctness reviewer, whom discopy-bot calls once the
  style review has nothing to say. Inference runs on an open-weights
  model behind an OpenAI-compatible gateway, configured by the
  `STYLE_REVIEW_BASE_URL` and `STYLE_REVIEW_MODEL` repository variables and
  the `STYLE_REVIEW_API_KEY` secret
  ([#608](https://github.com/discopy/discopy/pull/608)).
- Combinatorial map representation, `discopy.cmap`, encoding diagrams in
  compact categories as a permutation on the ports of each box
  ([#338](https://github.com/discopy/discopy/pull/338)).
- Syntax and drawing for 2-categories
  ([#354](https://github.com/discopy/discopy/pull/354),
  [#355](https://github.com/discopy/discopy/pull/355)).
- `Transformation` in `discopy.cat`, the natural transformations between
  functors ([#351](https://github.com/discopy/discopy/pull/351)).
- `cat.Equation` with an argument `up_to` for computing quotients
  ([#415](https://github.com/discopy/discopy/pull/415)).
- Ribbon diagram support with configurable wire spacing
  ([#358](https://github.com/discopy/discopy/pull/358)).
- Opt-in colour legend for drawings
  ([#357](https://github.com/discopy/discopy/pull/357)).
- Rich display hooks (`_repr_svg_`/`_repr_html_`) for `Diagram` and `Drawing`
  in Jupyter/IPython
  ([#445](https://github.com/discopy/discopy/pull/445)).
- Composition benchmark suite for diagram operations, reproducing the
  scaling experiments of arXiv:2105.09257
  ([#346](https://github.com/discopy/discopy/pull/346)).
- CMap cases for the composition benchmark suite, mirroring its Hypergraph
  workloads. Benchmark reports now include a per-suite Markdown table with
  a scaling plot.
- Conversion benchmarks between Diagram, Hypergraph and CMap representations.
- The benchmark job runs only on `main` and on pull requests labelled
  `benchmark` ([#385](https://github.com/discopy/discopy/pull/385),
  [#459](https://github.com/discopy/discopy/pull/459)).
- Diagram spacing is now automatically computed from exact font-dependent
  text width, for both box names and wire labels, instead of overflowing
  or colliding with neighbouring wires
  ([#364](https://github.com/discopy/discopy/pull/364),
  [#365](https://github.com/discopy/discopy/pull/365)).
- Explicit permutations in symmetric layers: `symmetric.P` supports the
  permutation operations and functorial semantics, while `symmetric.Layer`
  alternates permutations with generators without canonicalising diagram
  state ([#362](https://github.com/discopy/discopy/pull/362)).
- The category of parametric maps, `discopy.para`, wrapping morphisms
  `dom @ param -> cod` of any symmetric underlying category, with
  reparametrisation as a method and a subclass lifting each level of the
  hierarchy below symmetric: traced, Markov, closed, feedback, compact and
  hypergraph ([#558](https://github.com/discopy/discopy/issues/558),
  refactoring [#325](https://github.com/discopy/discopy/pull/325)).
- `para.Symmetric` carries an optional coparameter space: a map is
  `inside : dom @ param -> cod @ copar` with `copar` empty by default, so
  parametric maps read as before, coparametric maps are the empty-`param`
  case and the diagonal `param == copar` is the free category with feedback
  — the type of one time step of a `Stream`. The constructor reads
  `(dom, cod, inside, param, copar)` with both hidden spaces optional.
  Composition and tensor accumulate the hidden objects on both sides,
  `trace` and `feedback` route the coparameters out of the way and
  `recopar` post-composes them, covariantly where `reparam` is
  contravariant ([#572](https://github.com/discopy/discopy/issues/572)).
- The pivotal structure of `Rep(H)`: `HopfAlgebra.drinfeld_element`,
  `pivotal_element` and `ribbon_element`, cached single tensors named after
  the literature (Reshetikhin–Turaev; Kassel; Radford), with pivotal cups
  and caps twisting the dual leg so all four orientations are intertwiners.
  `taft(n)`, the smallest algebras with a pivot of order `n` (Sweedler's
  algebra is `n = 2`), realise the Kauffman–Radford ribbon criterion
  ([#484](https://github.com/discopy/discopy/pull/484)).

### Changed

- An axiom states its own verdict instead of deferring to a status table.
  A body returns `NotImplemented` when the structure does not apply, an
  `AxiomError` wrapping the equation when the law is known to be broken, and
  the equation itself otherwise, built with `cls.equation_factory` — or
  `cls.ob.equation_factory` when the law is about objects — so a class that
  quotients its equations quotients its axioms with it, and `cat.Ob`,
  `monoidal.Colour` and `Natural` gain the factory they were missing. The 79
  `axiom_status` entries become overrides that say what they mean where they
  mean it, and `AxiomStatus`, `Category.axiom_status`,
  `Category.axiom_equality`, the `eq` parameter of every axiom and the unused
  `strict` flag of `Axiom` are removed. An axiom that does not apply takes no
  argument, so its verdict is read before anything is generated.
- An axiom override never restates its equation, it is one assignment
  dispatching on the inherited law: `Axiom.modulo(up_to)` weakens it, as in
  `bifunctoriality = MonoidalCategory.bifunctoriality.modulo(normal_form)`;
  `Axiom.failing(reason)` declares it broken, wrapping the equation in an
  `AxiomError` carrying the reason; and `Axiom.inapplicable(reason)`
  declares it does not apply. Each returns a fresh `Axiom` that takes its
  name from the attribute through `__set_name__` and its arguments from the
  original signature. `Equation.modulo(up_to)` is the equation-level
  counterpart, named `modulo` since `up_to` is the attribute it rebinds.
  The comonoid and spider laws that no combinatorial map supplies are
  declared once on `cmap.CMap` rather than on each of `markov`, `closed`
  and `frobenius`.
- The property matrix follows the parametrised `CMap`: `balanced.CMap` and
  `pivotal.CMap` join the matrix as `cmap.CMap[balanced.Diagram]` and
  `cmap.CMap[pivotal.Diagram]`, and the five `braid_naturality` cells that
  xfailed on `CMap.to_diagram` refusing a traced box (#606) now pass.
  Structure restorations attach to each alias — `compact` and `frobenius`
  both restore currying and trace naturality — since subscripts do not
  inherit from one another, and `balanced.CMap.braid_naturality` is
  declared inapplicable: a map wires its braids symmetrically, which
  balanced diagrams have no swaps to decode.
- The property matrix is one parametrized test: every axiom of every
  carrier in `proptest.test_axioms.CARRIERS`, marked skip or xfail by
  its own verdict. Argument generation is dynamic dispatch on the axiom
  itself — `Axiom.strategy()` resolves the annotations of its parameters to
  the carrier's objects and arrows — so `proptest/strategies.py` and the
  per-module test classes disappear. The `--axioms` pytest flag selects
  matrix cells by glob, e.g. `--axioms 'compact.CMap.*'` or
  `--axioms '*.Diagram.unitality'`, with `*` as the only wildcard so that
  brackets match themselves. For quick debugging outside pytest,
  `Axiom.falsify()` searches for a shrunk counterexample to a bound axiom —
  arguments for which the verdict fails — raising `NoSuchExample` when it
  finds none.
- Every module's test file gets one `test_axioms` calling
  `testing.assert_axioms` on its carriers: each axiom is checked on a
  single example drawn from its own strategy, a dry run of the property
  tests, which replaces the `Arguments` table of `test/abc.py`.
- A `NamedGeneric` subscripted by a DisCoPy class takes its qualified name,
  e.g. `Hypergraph[monoidal.Diagram]` rather than `Hypergraph[Diagram]`,
  which every level's hypergraph printed alike — the property matrix ids
  are unique again. Foreign parameters keep their bare name: `Tensor[int64]`
  is what a user writes, and no two of them clash.
- The strategy tests live with what they test: every syntax module's test
  file gets a single `test_strategy` checking its strategy reaches each of
  its structural boxes through `testing.assert_strategy_finds`, and every
  argument generator of `discopy.testing` gets exactly one test in
  `test/testing.py` — valid arguments accepted, invalid ones rejected, the
  interesting shapes found — with `LeftCurrying` validating its evaluation
  boundary like every other generator. `proptest/` keeps the strict minimum
  for the property matrix, one file `test_axioms.py`, so
  `proptest/test_strategies.py` is removed along with the dead `--bugs`
  pytest option that read the removed axiom statuses. `markov.CMap` and
  `frobenius.CMap` join the matrix — `spider_fusion` declared inapplicable
  with the other spider laws that no combinatorial map supplies — while
  `PRO`, which has no strategy, leaves it.
- The five `*_typing` axioms and `self_dual` state equations between objects
  rather than lifting their types through `cls.id`, now that a body chooses
  its own equation factory rather than being handed one built from the arrow
  carrier.
- `CMap` is aligned on `Hypergraph`. It is parameterised by a category as
  `NamedGeneric["category"]` instead of carrying `require_*` flags, and it is
  always compact whatever category hosts it, so every compact operation is
  available when manipulating maps. The host category is asked for structure
  only on the `to_diagram` downgrade path, i.e. in `make_monogamous`, which
  needs cups and caps, and in `make_causal`, which reorders acyclic maps
  without traces and only asks for traces when cycles or scalar loops remain,
  cutting every backward wire and loop at once. Each box is placed where its
  first domain wire already is, so the decoder no longer swaps that wire to
  the front.
  The predicates follow the `Hypergraph` names and are local conditions on
  the edges, `__init__` takes a keyword `check`, and `curry`, `uncurry` and
  `ev` come from the cups and caps of `abc.RigidCategory` when the host
  category is rigid and stay explicit boxes otherwise, all three defaulting
  `left` to `True` like the rest of the hierarchy. `CMap.eval` delegates to
  the `eval` of the host category, e.g. contracting a tensor map in a
  single `einsum`, instead of `tensor` grafting it onto its `CMap` alias
  ([#532](https://github.com/discopy/discopy/pull/532),
  [#560](https://github.com/discopy/discopy/issues/560)).
- `uncurry` is defined once in `abc.BiclosedCategory`, in terms of a new
  method `base_and_exponent` for the two objects that `ev` evaluates.
  `abc.RigidCategory` and `cmap.CMap` override that method instead of
  duplicating the composition with `ev`: a pregroup has no exponential
  object, so its exponent is the `n` objects at the end resp. the start of
  the codomain, dualised, and a map reads it off its wiring when the host
  category is rigid ([#532](https://github.com/discopy/discopy/pull/532)).
- `balanced` and `pivotal` export a `CMap` alias like the other levels of
  the hierarchy ([#532](https://github.com/discopy/discopy/pull/532)).
- `Hypergraph.to_diagram` raises `messages.NOT_RIGID/FROBENIUS/TRACED/...`
  where it checks that the category has the wiring structure
  ([#532](https://github.com/discopy/discopy/pull/532)).
- `Swap` is now the two-wire transposition subclass of `Permutation`, and
  constructing `Permutation(x @ y, [1, 0])` returns a `Swap`. A swap is
  plumbing like any other permutation: it coalesces with its neighbours in
  a `symmetric.Layer`, so a whiskered swap is stored and drawn as one wider
  permutation, and `foliation` composes consecutive layers of pure plumbing
  into one, unless they compose to the identity. The pictures stay the same:
  a permutation no longer re-labels a wire it keeps in place, nor pushes its
  input labels off the canvas, so the redrawn baselines only differ by their
  serialisation, except `symmetric/foliation.svg` (input labels come back on
  canvas), `int/symmetric-feedback.svg` (one row taller) and
  `symmetric/yang-baxter.svg` (gains its foliated middle)
  ([#444](https://github.com/discopy/discopy/issues/444)).
- The quantum `SWAP` is a gate rather than the symmetry of the category, so
  that a physical swap is distinguishable from a logical one. It is a
  `QuantumGate` drawn as a crossing, while `Circuit.swap` still gives the
  plumbing `quantum.circuit.Swap`: the two evaluate to the same array but
  only the gate survives compilation, `to_tk` emitting `OpType.SWAP` for
  the gate while compiling a logical swap away by applying later gates to
  the permuted qubits.
  `discopy.quantum` exports both, `discopy.quantum.gates` only the gate.
- `monoidal.Layer` holds a list of boxes and non-empty types with at least
  one box and no two consecutive types, instead of an odd-length list
  alternating type and box. Whiskering extends the list only when the type
  is non-empty and the outermost element is a box, otherwise it merges into
  the boundary type, and tensoring two layers merges a trailing type with a
  leading one. The constructor type checks and normalises to restore the
  invariant unless it is called with `normalise=False`, which the internal
  call sites do, so tensoring `n` layers is linear rather than quadratic.
  `Layer` is a `ColouredMonoid`, i.e. it defines `tensor` and inherits `@`
  and its right-whiskering mirror from it, embedding types and boxes as
  layers, and `Layer.cast` is removed since `Layer(box)` already builds the
  singleton layer. `symmetric.Layer` follows with "permutation" in place of
  "type". `Diagram.interchange` checks its preconditions up front, so an
  out-of-range index raises `IndexError` and a diagram with more than one box
  in a layer raises `NotImplementedError` even when `i == j`
  ([#438](https://github.com/discopy/discopy/pull/438)).
- `Arrow` is refactored onto a `FreeCategory` base class
  ([#350](https://github.com/discopy/discopy/pull/350)).
- The `tensor` module is refactored to go through `CMap` for `einsum`
  ([#402](https://github.com/discopy/discopy/pull/402)).
- Add a `functor_factory` attribute to each `Diagram` class and remove
  `hypergraph_factory` and `map_factory`: `Hypergraph` and `CMap` are
  parameterised directly as `NamedGeneric["category"]`
  ([#379](https://github.com/discopy/discopy/pull/379),
  [#532](https://github.com/discopy/discopy/pull/532)).
- Documentation notebooks are migrated from Jupyter (`.ipynb`) to marimo
  markdown, with docs (`nbsphinx` → embedded marimo HTML) and CI
  (`nbmake` → `marimo export`) updated to match
  ([#404](https://github.com/discopy/discopy/pull/404)).
- The `Functor` keyword arguments `ob`/`ar` are renamed to
  `ob_map`/`ar_map` throughout the codebase, docs and benchmarks
  ([#369](https://github.com/discopy/discopy/pull/369),
  [#411](https://github.com/discopy/discopy/pull/411),
  [#417](https://github.com/discopy/discopy/pull/417)).
- `Ty.name` is a cached property computed from its `inside`
  ([#421](https://github.com/discopy/discopy/pull/421)).
- SVG drawings are made deterministic by ordering spiders and boxes
  reproducibly
  ([#457](https://github.com/discopy/discopy/pull/457),
  [#469](https://github.com/discopy/discopy/pull/469)).
- Documentation images are converted from PNG to SVG and checked in as
  drawing-test baselines: there are no separate test images anymore,
  every image in the docs doubles as a drawing test
  ([#419](https://github.com/discopy/discopy/pull/419),
  [#435](https://github.com/discopy/discopy/pull/435),
  [#463](https://github.com/discopy/discopy/pull/463),
  [#470](https://github.com/discopy/discopy/pull/470)).
- The `test/` directory is reorganised to mirror `discopy/`
  ([#403](https://github.com/discopy/discopy/pull/403)).
- Symmetric categories generate their swaps with `swap_factory` rather than
  `braid_factory`, which is now a `classproperty` reading it
  ([#440](https://github.com/discopy/discopy/pull/440)).
- `abc.SymmetricCategory` extends `abc.BraidedCategory` directly, so
  symmetric and Markov categories are not required to implement `twist` and
  `trace`; balanced categories stay traced, and the two branches meet again
  in `abc.CompactCategory` where the twist is the identity. The free diagram
  classes keep their freely interpreted traces by subclassing
  `traced.Diagram` ([#349](https://github.com/discopy/discopy/issues/349)).
- `abc.ColouredMonoid.unit` takes a colour and may return an object of `C0`
  rather than an element of `C1`, since the unit of a coloured monoid is the
  identity on a colour and need not belong to the monoid. `monoidal.Layer`
  overrides it to give the empty type: a layer has at least one box, so
  `Layer()` raises and `Layer.unit()` used to raise with it, while
  `Layer.unit(colour)` is now the empty type that `tensor` accepts on either
  side ([#568](https://github.com/discopy/discopy/issues/568)).
- `monoidal.Layer.id` raises instead of building a layer of empty plumbing,
  which denoted the identity diagram while not being the empty sequence of
  layers: inside a `Diagram` it survived `normal_form`, compared unequal to
  `Diagram.id` and made `foliation` and `draw` raise. `Layer.whisker` leaves a
  type as a type and `tensor` merges it into the boundary, so whiskering never
  builds one. Passing `normalise=False` still does, which is left as an
  explicit opt-out of the invariant
  ([#599](https://github.com/discopy/discopy/issues/599)).
- `biclosed` defaults `left` to `True` in `Diagram.curry`, `Diagram.ev`,
  `Diagram.uncurry`, `CMap.curry` and `CMap.uncurry`, so that `abc`,
  `biclosed`, `closed` and `rigid` all agree on one convention: the default
  exponential is `Over`, i.e. `<<`. Previously `closed` inherited
  `curry` defaulting to the right from `biclosed` while overriding `ev` to
  the left, so the default currying was never evaluated by the default
  `ev`. Code relying on the old right-handed default should pass
  `left=False` explicitly
  ([#560](https://github.com/discopy/discopy/issues/560)).
- Benchmarks compare two commits measured on the same runner rather than a
  committed baseline, so no baseline is stored in the repository and no
  normalisation is needed to account for the CPU model a GitHub-hosted runner
  happens to give out. A pull request compares its head against its base, a
  push to `main` against the branch before the push. The comparison goes to
  the job summary and, on a pull request, to a comment listing the regressions
  and speedups over 25%; a regression raises a warning annotation and never
  fails the job, since a shared runner can push an unrelated case over the
  threshold on noise alone.
- Benchmark cases now use `pytest-benchmark`'s automatic calibration.
- Every `monoidal.Wire` subclass named `Ob` is renamed to `Wire`: `rigid`,
  `braided`, `biclosed`, `pivotal`, `frobenius`, `feedback` and
  `quantum.circuit`, completing the rename that introduced `monoidal.Wire`;
  `cat.Ob` keeps its name. Accessing the old name still works, returning the
  new class with a `DeprecationWarning` through a module-level `__getattr__`
  (`utils.deprecated_ob`), on those seven modules and on `compact` and
  `grammar.pregroup` which re-exported it; trees serialised with an `Ob`
  factory string load the same way
  ([#566](https://github.com/discopy/discopy/pull/566)).

### Fixed

- `Diagram.foliation` falls back to merging layers when `to_hypergraph`
  is partial — a boundary-disconnected pivotal diagram, whose rejection
  is by design — instead of crashing.
- The quantum cells caught five bugs, fixed here: `quantum.Swap` could
  not unpickle (`Box.__setstate__` demanded a mixedness the plumbing
  never stores); `Ket` and `Bra` inherited the `(name, dom, cod)` repr
  their bitstring `__init__` rejects; `zx.H` carried an unpicklable
  lambda as its dagger and is now a `Hadamard` class, its own dagger;
  `zx.Swap` reprs itself qualified instead of as a bare `SWAP` that
  collides with the quantum gate, and `zx.Spider`, `Scalar` and
  `Hadamard` serialise to trees; and `QuantumGate` normalises the signed
  zeros of its complex data, whose reprs made numerically equal gates
  compare unequal.
- `Matrix.braid` is a `classproperty` reading `cls.swap` instead of a
  static binding of `Matrix.swap`, so `Tensor.braid` dispatches to the
  `Dim`-typed swap instead of crashing on `'Dim' object cannot be
  interpreted as an integer`; `Tensor.copy` defaults `n=2` like the
  `Matrix.copy` it overrides; `Dim` serialises to a tree (its atoms are
  bare integers, which the type serialisation used to choke on); and
  `Dim.unwind` returns itself, so the hypergraph of a tensor diagram no
  longer crashes on an atom without a winding.
- `Copy.dagger` and `Merge.dagger` build through the level's
  `merge_factory` and `copy_factory` instead of the bare markov classes,
  and `closed` gains the `Merge` it was missing: the dagger of a
  `closed.Copy` used to be a `markov.Merge` that closed diagrams reject.
  `Feedback.dagger` raises `AxiomError` — the delay of its memory is not
  reversible — where it used to crash with a `TypeError` from the generic
  bubble reconstruction.
- Tree serialisation of the structural boxes: `Trace`, `Feedback`,
  `Twist`, `Braid` with `is_dagger`, `Copy`, `Merge`, `Discard`,
  `Spider`, `Eval`, `Coeval` and `Curry` used to raise (or lose the
  dagger) on `to_tree`/`from_tree`, inheriting a serialisation whose
  keys their `__init__` does not accept, so `dumps`/`loads` crashed on
  any diagram containing one.
- `Diagram.to_staircases` builds its layers with `functor_factory`
  instead of the bare `monoidal.Functor`, which rebuilt a `Trace` as a
  `monoidal.Bubble` that the level's diagram class then rejected — so
  `foliation` crashed on any traced diagram.
- `Hypergraph.to_graph` keys a spider node by the spider's own type
  rather than the boundary's, which created a phantom, attributeless
  node when a boundary wire reads an adjoint of its spider type — so
  `hash` crashed with `KeyError: 'box'` on such hypergraphs.
- Pickling an instance of a subscripted `NamedGeneric` — a `Matrix[int]`,
  `Tensor[float]`, `Hypergraph[...]` or `CMap[...]` — loads back with its
  type parameter again: the `__setstate__` restoring the subscript was
  defined on `NamedGeneric` itself, which the classes its subscripts
  create do not inherit from, so every such instance unpickled as its
  bare origin class — `Matrix[int]` came back as a `Matrix` with no
  `dtype`, and comparing a loaded `Hypergraph` raised `AttributeError`.
  `tensor.Box.__setstate__`, the one caller that worked around this by
  invoking the method explicitly, now lets its `super` chain restore the
  subscript.
- `markov.Copy` and its subclasses, `Discard` included, can be unpickled:
  `Copy.__new__` required the copied type as argument, which the pickle
  protocol's bare `__new__(cls)` call does not pass.
- `traced.Trace`, `biclosed.Eval`, `Coeval` and `Curry` (and their
  subclasses in `closed`) satisfy `eval(repr(x)) == x`: `Trace` printed
  `str` instead of `repr` of its argument, and the other three inherited
  the `(name, dom, cod)` repr of `Box`, which their `__init__` does not
  accept.
- A `Cat`-valued functor applies to objects again: with `Functor.ob` now
  `abc.Category` rather than `type[Category]`, the image of an object may
  be a class implementing it, which `Functor.__call__` returns as is
  instead of trying to instantiate `Category`. This was breaking the
  `diagrams` notebook.
- `braided.Diagram`, `rigid.Diagram` and `ribbon.Diagram` register their own
  `functor_factory`, which they defined but never assigned, so a functor out
  of them builds diagrams of their own class instead of their base's.
- `Diagram.strategy` chains its layers instead of drawing every boundary up
  front, so the first layer is generated without boundary constraints and
  the property matrix reaches the structural boxes of each category:
  swaps, permutations, braids, twists, cups, caps and traces never appeared
  inside a generated diagram before. This immediately shows that
  `CMap.to_diagram` cannot convert back a map with a traced box, which
  makes `braid_naturality` a `"bug"` for symmetric and closed maps.
- `TracedCategory.trace_dinaturality_left` and `trace_dinaturality_right`
  state sliding between two distinct traced objects, as
  `Tr^x(f ; b @ g) == Tr^y(a @ g ; f)` for `g: y -> x`, instead of tracing
  the wrong wires of a single object. Symmetric diagrams and everything
  below them now check them up to hypergraph rather than skipping them.
- `FeedbackJoining` generates two units of memory drawn independently and
  validates the boundaries of its arrow rather than calling the very
  `feedback` it is testing, so the property matrix reaches heterogeneous
  memory and records that `feedback.Diagram.feedback` unrolls it in the
  wrong order ([#606](https://github.com/discopy/discopy/issues/606)).
- `Diagram.normal_form` expands multi-box layers into staircases before
  normalization, so connected foliated diagrams normalize without raising.
- Pivotal diagram-to-map conversion now encodes cups and caps as `CMap`
  wiring rather than keeping them as boxes
  ([#532](https://github.com/discopy/discopy/pull/532)).
- `CMap.cups` and `CMap.caps` now require the handedness of the host category,
  i.e. `cups(x, x.r)` and `caps(x.r, x)`, so that these factories reject badly
  oriented cups and caps, rather than fixing the handedness at downgrade time.
  ([#532](https://github.com/discopy/discopy/pull/532)).
- `Hypergraph.explicit_trace` and `CMap.explicit_trace` no longer mistake the
  inherited `trace_factory` of a user-defined subclass for a class method,
  which used to raise `AttributeError: type object 'Trace' has no attribute
  '__func__'` ([#532](https://github.com/discopy/discopy/pull/532)).
- `CMap.topological_order` raises `AxiomError` on a map with a directed
  cycle, where it used to crash with `TypeError` on the `None` returned by
  `box_ranks` ([#532](https://github.com/discopy/discopy/pull/532)).
- `Hypergraph.to_diagram` no longer asks for swaps when one of their two
  sides is empty, where the identity does
  ([#532](https://github.com/discopy/discopy/pull/532)).
- A boxless `monoidal.Layer` can no longer be placed inside a `Diagram`:
  `Diagram.__init__` raises `ValueError` for a layer with no box, restoring
  the invariant that every layer holds at least one box and that the identity
  diagram is the empty sequence of layers. Such a layer is the internal unit
  of `Layer.tensor`, built by `Layer.id` and merged away by `Layer.normalise`;
  put inside a diagram by hand it survived `normal_form` and made `foliation`
  and `draw` raise. The check is gated on `_scan`, so the internal fast paths
  that build layers by construction are unaffected
  ([#599](https://github.com/discopy/discopy/issues/599)).
- `review.py`'s style-review request: `ask` used to let a gateway
  `HTTPError` propagate without reading its body, so a 400 gave no clue
  whether it meant a dead model slug or an oversized prompt; it now prints
  the response body before re-raising. `assemble` used to budget the raw
  file texts against `BUDGET`, but `numbered`'s line-number prefixes, the
  per-file headers, `prompt.md` and `STYLE.md` were all added on top,
  uncounted, so the assembled prompt could exceed `BUDGET` on a PR
  touching a large module even when its diff was small; every part is now
  budgeted as assembled. `ask` also used to unconditionally send
  `"reasoning": {"enabled": False, "exclude": True}`, which not only 400s
  on models that mandate reasoning (e.g. `stealth/ox-alpha`, with
  "Reasoning is mandatory for this endpoint and cannot be disabled") but
  measurably hurt review quality by forcing it off; `ask` no longer sends
  the `reasoning` field at all, leaving it to each model's own default,
  with `max_tokens` raised from 8,192 to 32,768 so reasoning tokens don't
  starve the answer, and it now logs `finish_reason`/`usage` on every
  response and the raw answer on a JSON-parse failure, so a truncated or
  malformed answer is diagnosable instead of a bare traceback
  ([#611](https://github.com/discopy/discopy/issues/611)).
- `build.yml` timeouts and a bounded, retried Graphviz install
  ([#591](https://github.com/discopy/discopy/issues/591)).
- Boundary-constrained arrow strategies can generate composite paths, layer
  strategies honour box exclusions, and combinatorial-map strategies preserve
  subclasses. The abstract feedback signature now matches its inferred-argument
  implementations.
- `frobenius.Diagram.unfuse`'s doctest no longer sets `Spider.color = "red"`
  to draw its example, which was leaking into every later doctest in the
  same pytest process
  ([#522](https://github.com/discopy/discopy/issues/522)).
- Tensor networks are contracted with `opt_einsum` when the number of
  indices exceeds `numpy.einsum`'s 52-index limit
  ([#448](https://github.com/discopy/discopy/pull/448)).
- `grammar.categorial.cat2ty` reads a fully parenthesized category such as
  `(S\NP)` as a category rather than an atom, strips CCGbank features
  wherever they occur rather than on atoms only, and associates slashes to
  the left as CCG does
  ([#528](https://github.com/discopy/discopy/issues/528)).
- Non-linear terms in `discopy.closed`: an `Application` with no free variables
  builds instead of raising, and its free variables keep first-occurrence order
  rather than going through a set whose iteration order depends on hashing
  ([#542](https://github.com/discopy/discopy/issues/542),
  [#543](https://github.com/discopy/discopy/issues/543)).
- `closed.Abstraction` discards a variable that does not occur in the body
  instead of raising, and nested abstractions curry the abstracted wire rather
  than the first one, so `eval` preserves `dom` and `cod`
  ([#541](https://github.com/discopy/discopy/issues/541),
  [#544](https://github.com/discopy/discopy/issues/544)).
- `biclosed.Application` lists its free variables in the same order as the
  wires of its `dom`, so that `Abstraction` strips the right end of it and
  `eval` preserves both `dom` and `cod`
  ([#550](https://github.com/discopy/discopy/issues/550)).
- Hypergraph hash
  ([#387](https://github.com/discopy/discopy/pull/387)).
- Bubble drawing
  ([#431](https://github.com/discopy/discopy/pull/431)).
- Controlled gate drawing: the control wire is anchored on the indexed
  input of the controlled box rather than its first one, so gates with a
  classical wire or a distance other than one are drawn on the right wires
  ([#439](https://github.com/discopy/discopy/pull/439)).
- Drawing a discard on more than one wire: `draw_discard` was shadowing the
  layer index with its inner loop counter
  ([#513](https://github.com/discopy/discopy/issues/513)).
- `closed.Context.dom` called `category.ob.tensor` unbound, which raised
  `TypeError` for an empty context instead of returning `Ty()`
  ([#549](https://github.com/discopy/discopy/issues/549)).
- `python.additive.Function.trace` fed a looping output tag straight back
  in as an input tag, reading the wrong traced summand (or raising
  `IndexError`) whenever `dom` and `cod` have different lengths
  ([#554](https://github.com/discopy/discopy/issues/554)).
- Both branches of `closed.Abstraction.eval` curry on the right: the
  context branch curried out the wrong end of its domain, so an abstraction
  applied to an argument sharing a free variable did not compose, and a
  left abstraction evaluates through its right counterpart
  ([#562](https://github.com/discopy/discopy/issues/562)).
- `Tensor.spider_factory` returns its array on the active backend instead
  of always on NumPy, so diagrams with spiders evaluate — and
  differentiate — under the PyTorch backend
  ([#582](https://github.com/discopy/discopy/issues/582)).
- `trace(0)` is the identity, i.e. the vanishing axiom, rather than a
  morphism with empty `dom` and `cod`: `x[:-n]` is the empty prefix at
  `n == 0`, which emptied the boundary of `Hypergraph.trace` and of both
  `python.Function.trace`, and made `rigid.Diagram.curry(0, left=True)`
  curry the whole domain
  ([#578](https://github.com/discopy/discopy/issues/578)).
- Closed and biclosed diagrams containing a `Copy`, `Merge`, `Swap`,
  `Permutation`, `Braid` or `Twist` can be drawn: the `markov`, `symmetric`,
  `braided` and `balanced` functor branches now check that the codomain has
  the structure before using it, the way `biclosed.Functor` already did for
  `ev`, `exp` and `curry`
  ([#491](https://github.com/discopy/discopy/issues/491),
  [#548](https://github.com/discopy/discopy/issues/548)).
- `Double`'s `H*` structure is built by transposition instead of the dagger,
  which wrongly conjugated complex structure constants — invisible on the
  real examples of #405, wrong for `taft(3)`
  ([#484](https://github.com/discopy/discopy/pull/484)).

### Performance

- The elements of a Hopf algebra (`drinfeld_element`, `pivotal_element`,
  `ribbon_element`) contract each structural generator once through the
  cached `Algebra.arrays` and solve for the pivot with a thin SVD, so that
  `Double(taft(3)).ribbon_element` takes under a second instead of twenty
  ([#484](https://github.com/discopy/discopy/pull/484)).
- `Ty` construction is sped up with `assert_isinstance` and lazy naming
  ([#420](https://github.com/discopy/discopy/pull/420)).
- `Hypergraph` equality, permutations and other micro-optimizations bring
  equality checks down to `O(n)`
  ([#353](https://github.com/discopy/discopy/pull/353)).
- `CMap.from_diagram` is linear rather than quadratic in the number of
  boxes: `CMap.from_glued` glues the image of each box onto a scan of
  open wires in a single pass, instead of folding the images with
  `then` and re-validating the whole prefix at every step. This speeds
  up `Diagram.eval` on every tensor backend
  ([#525](https://github.com/discopy/discopy/pull/525)).

### Project

- The unit suite starts its purification: tests that restate cells of the
  property matrix on hand-picked examples — the category axioms called
  verbatim on maps, the then/tensor and interchange families, swap
  elimination, cup-cap zipping, curry/uncurry and trace roundtrips,
  functor preservation and permutation unitality — are deleted from
  `test/`, keeping their validation raises, encoding pins and issue
  regressions. Measured on this tree, `proptest/` alone covers 54% of
  `discopy/` against 98% for the unit suite with its doctests: the gap is
  the baseline the next phases ramp by enrolling new carriers and ad-hoc
  properties, deleting each unit test as a property subsumes it.
- The `TODO.md` rule of `RULES.md` is split in two: creation stays point 1,
  and a new point 2 has the agent delete its own `TODO.md` once every
  point is `[x]` or filed as an issue, taking the pull request out of draft:
  the style reviewer gives it a first pass before a human deep-reads it.
  A round of review feedback — bot or human — starts a fresh `TODO.md`,
  deleted again when the round is done; nitpicks are just fixed and
  resolved. Rule 4, only talk when prompted, is removed
  ([#608](https://github.com/discopy/discopy/pull/608)).
- `AGENTS.md`/`CLAUDE.md`/`RULES.md`/`STYLE.md` introduced and iterated on,
  and `CONTRIBUTING.md`/`README.md` updated to match, to describe the
  collaboration and coding protocol for AI agents working on the repo
  ([#378](https://github.com/discopy/discopy/pull/378),
  [#422](https://github.com/discopy/discopy/pull/422),
  [#428](https://github.com/discopy/discopy/pull/428),
  [#471](https://github.com/discopy/discopy/pull/471),
  [#477](https://github.com/discopy/discopy/pull/477),
  [#481](https://github.com/discopy/discopy/pull/481)).

## [1.2.2] - 2025-12-19

See the [GitHub release](https://github.com/discopy/discopy/releases/tag/1.2.2).

## Older releases

See the [GitHub releases page](https://github.com/discopy/discopy/releases)
for the changelog of `1.2.1` and earlier.
