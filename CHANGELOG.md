# Changelog

All notable changes to DisCoPy are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Changes since [`1.2.2`](https://github.com/discopy/discopy/releases/tag/1.2.2).

### Added

- Every level declares the generators it binds after its `Diagram` as
  class variables of it, e.g. `swap_factory: ClassVar[type["Swap"]]` in
  `symmetric.Diagram`, so that a typechecker reads `cls.swap_factory` as
  the class it is rather than as unknown, and binds `box_factory` to its
  own `Box`. `pivotal.Box` is a `traced.Box`, as its diagrams are traced,
  and `ribbon.Diagram.sum_factory` is `ribbon.Sum`, which it defined but
  never assigned
  ([rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1)).
- `discopy.kleisli.token`, probabilistic token passing on lambda terms: a
  `Machine[M]` interprets the constants of a `closed` term, one transition
  of the token is a `kleisli.additive.Channel` from an entry plus the two
  directions the token travels in to an exit plus the same two, and the
  machine is its trace, i.e. the execution formula walks the token until it
  leaves. Following Dal Lago & Hoshino's [Geometry of Bayesian
  Programming](https://arxiv.org/abs/1904.07425), the worked example is
  the discrete analogue of their calculus' two constants: `sample` draws a
  coin's bias from a prior and `score` multiplies the weight of the branch
  it runs in, so the mass the token has left is the evidence and dividing
  by it is Bayes' rule. The machine is generic in the monad, hence also
  nondeterministic over `Powerset` and partial over `Maybe`. Half of
  [#618](https://github.com/discopy/discopy/issues/618), whose `Hypergraph`
  evaluation methods are still to come
  ([#639](https://github.com/discopy/discopy/pull/639)).
- `discopy.neural.signature`, what a generator promises. `Sym` is the
  symmetry an orbit of legs carries: none, the symmetric group or the
  cyclic one. `Orbit(role, arity, sym, traced)` is a family of legs playing
  one atomic role, each leg twice when traced, the outgoing copy before the
  incoming one. `Signature(orbits)` is the legs of one generator in port
  order, with `cod` the type of its abstract box in `discopy.frobenius`,
  `box`, `positions`, `loops`, `loop_wires` and `resize`, which changes the
  arity of one orbit so that one shared module serves sites of different
  degree. `generators` are the permutations of ports generating the
  symmetry group an equivariance check runs a module against, and
  `leg_generators` the same generators as permutations of legs, before
  they act on ports. `from_incidence` draws the bipartite incidence graph
  of nodes and relations, with non-uniform degrees and a name and a
  signature per relation; `from_relation` draws the graph of a symmetric
  irreflexive binary relation. Both close the traced loops and draw in
  `frobenius`: every box they wire has an empty domain, so every wire
  joins two codomain ports, which a map accepts only between self-dual
  roles. They go through `cmap.CMap.from_wiring`, a closed map from boxes
  and wires between `(box, port)` pairs counted in `CMap.logical_order`,
  domain ports then codomain ones, refusing a port wired twice, to itself
  or not at all; both methods come back from the history of #736, where
  the redesign left them with nothing to consume them. The module is
  discopy#739 re-cut onto the feedforward base. The flat layout of its
  geometry-of-interaction backend, `slices` and `width`, and the composite
  legs that only it needed do not come: a `Box` here reads one tensor per
  leg, and `positions` says which ports a role's legs are
  ([#739](https://github.com/discopy/discopy/pull/739)).
- Hypergraphs of Python functions: `Hypergraph[python.Function]` is the
  hypergraph category over `python.Function`, its spiders labelled by atomic
  `List[type]` and its boundaries by lists of them: `monoidal.List` gains
  `is_atomic` and `unwind` like `Ty`, the two methods `Hypergraph.__init__`
  asks of a spider type, so that the spiders of a hypergraph over any free
  monoid are checked alike. `Hypergraph.__call__` evaluates a
  left-monogamous causal hypergraph by calling the boxes in order, copying
  and discarding the values as the wiring dictates and reading the number
  of outputs of a box off its codomain, so that a single output of type
  `tuple` is one value, and raises `AxiomError` saying which of the two it
  is not otherwise; a wiring with the wrong number of wires for a boundary
  raises a `ValueError` saying so, where it was bare. The new
  `hypergraph.Functor` maps the spider types and the boxes of a hypergraph
  while keeping its wiring, a composite object atom by atom so that a raw
  callable in its `ar_map` is wrapped into a function of the right type,
  e.g. a hypergraph of a free symmetric category to one of Python functions,
  with the swaps absorbed into the wiring; its tests evaluate the carry-save
  adder of the composition benchmark exhaustively this way
  ([#363](https://github.com/discopy/discopy/pull/363)).
- `CMap.permutation`, a permutation encoded as boundary wiring: one
  fixpoint-free involution pairing each input port with the output port
  its wire lands on, so the map has no boxes and `2n` ports for `n`
  wires, where the default of `abc.SymmetricCategory` composes one `swap`
  per object, moving it across the ones before it, so it builds and
  composes as many maps of the whole boundary, quadratic in the number of
  wires. It is the composite of swaps, i.e. equals
  `Diagram.permutation(xs, doms).to_map()`, and takes its objects as a
  sequence or as one type like the default
  ([#735](https://github.com/discopy/discopy/issues/735)).
- `discopy.neural`, neural networks as diagrams: `discopy.neural.network`
  is the traced category of feedforward networks. `Dims` is the free
  monoid over the multiplicative `Dim`, i.e. a list of shapes with
  concatenation as tensor and the product of shapes distributing over it,
  the free rig on the natural numbers; `Network` is the free traced
  Markov category on `Box` layers of any input and output legs, each
  carrying an optional `module`, so that a residual block is a `copy` and
  a recurrent cell a `trace`. A feedforward network compiles:
  `Box.forward` applies the module of a layer to one tensor per leg, with
  `Dims.check` checking the shape of each tensor against its leg;
  `Network.to_function` is the functor into `python.Function` sending
  every leg to a tensor type and every box to its `forward`, with the
  copy, discard and swap of tuples, which `jax.jit` and `jax.grad` take as
  it is; and `discopy.neural.torch.Module` runs it as a PyTorch module
  with the modules of the boxes as its submodules, `torch.compile`
  included. A trace does not compile yet, and `import discopy.neural`
  imports no framework. `monoidal.Functor` reads a `Dim` that generates
  the types of its domain as one generator rather than factor by factor,
  so that functors, drawings and hypergraphs of networks map each leg as
  a whole ([#702](https://github.com/discopy/discopy/issues/702),
  [#736](https://github.com/discopy/discopy/pull/736),
  [#743](https://github.com/discopy/discopy/pull/743)).
- `biclosed.TermBase.alpha_eq`, the alpha-equivalence of lambda terms,
  i.e. equality up to the names of their bound variables, of any number
  of terms in one pass: the helper `alpha_eq_under` carries a scope for
  each term, mapping its bound variables to the depth of their binder,
  i.e. their de Bruijn level, extended in place on entering a binder and
  restored on leaving it, so the terms are alpha-equivalent when they are
  equal with their bound variables read as levels and the check is linear
  in the size of the terms, neither a renamed copy nor a fresh variable
  at any binder. Free variables are compared by name, bound ones by their
  level, applications by their `left` flag and abstractions by the type
  they bind; `closed` terms inherit it and `grammar.categorial`'s type
  raisings and binary compositions recurse into their subterms, as do
  `closed`'s tuples and projections, and a `let` statement binds its
  variables at the levels of its binder as an abstraction binds one,
  both through `TermBase.alpha_eq_bound`, which extends the scopes and
  restores them. Terms are `Testable` in the
  sense of `discopy.axioms`: `TermBase.generate` builds a planar linear
  term of a given type from a sequence of choices and the letters naming
  its bound variables, through a `Sampler` with one method per kind of
  node and the options of a choice deferred as closures, so that a term
  nests as deep as the recursion limit allows, linear and planar for
  `biclosed`, free to copy and discard for
  `closed`, `TermBase.strategy` draws them and `Renamed[C]`
  draws one shape under several namings, so that the laws of
  alpha-equivalence are axioms of `TermBase` checked by the property
  matrix, where `biclosed.TermBase` and `closed.TermBase` are now
  enrolled. `TermBase` is an `axioms.Equivalence`, the abstract class of
  a type with an equivalence relation besides equality, which states
  reflexivity, symmetry and transitivity once for any such relation: the
  relation is the `Equation` subclass `equivalence_factory`, which holds
  when its terms are related, `biclosed.AlphaEquation` here, and the two
  laws that need related terms quantify over `Related[C]`, two instances
  related by construction and a third that may not be, drawn by the
  type's `related`, so that each verdict runs both ways. Then the laws of
  alpha-equivalence itself: renaming, congruence with respect to
  application and to abstraction, soundness for evaluation, and
  completeness: two terms are
  alpha-equivalent exactly when regenerating each under one naming of
  its bound variables gives equal terms, drawn by `Canonical[C]` as two
  shapes under their own namings and under the canonical one, the one
  law an `alpha_eq` that says yes too often fails where the others hold
  of it. `Testable.axioms`, the laws a type inherits by name, moves there
  from `abc.Category`, so that any testable type has them.
  `Testable.serialisation`
  is declared
  failing on terms, which do not read back from their tree
  ([#692](https://github.com/discopy/discopy/issues/692)), and
  `Axiom.failing` reports a broken law whose terms fail to build as an
  `AxiomFailure` carrying the error rather than letting it escape.
  `biclosed.Ty.strategy` generates exponentials as well as atoms
  ([#767](https://github.com/discopy/discopy/pull/767)).
- `grammar.abstract`, abstract categorial grammars after de Groote's
  *Towards abstract categorial grammars* (2001)
  ([#398](https://github.com/discopy/discopy/issues/398)).
- `grammar.proofnet`, parses as proof nets: a `Sequent` is words with their
  abstract types and a goal, its ports are the atoms of the types with their
  polarity, and a `ProofNet` links each negative port to a positive port of
  the same atom. `ProofNet.from_term` is the axiom linking of a closed linear
  term and `ProofNet.to_term` reads its beta-normal eta-long term back from
  the goal, failing exactly when the net is not correct, so that two linear
  terms have the same net if and only if they are equal up to beta and eta.
  Equal words are told apart by order only: `from_term` gives each
  occurrence of a constant the first equal word no earlier one took, so
  words whose links matter, e.g. the two `the` of a sentence, should be
  distinct constants, with their position as `data`. `Sequent.decode`
  takes the linking of maximum score, block by block with `hungarian`, an
  assignment solver in numpy.
- `grammar.neural`, a parser into proof nets with PyTorch, over the states
  of any encoder: a constructive `Tagger` writing the type of each word in
  the Polish notation of a `Signature`, only ever writing what can be
  completed into a type, and a bilinear `Linker` trained on the likelihood
  of the gold linking after `sinkhorn` normalisation, jointly in `Parser`.
  Moved from the trilingual parser of
  [rel-int/lambek#8](https://github.com/rel-int/lambek/pull/8), without its
  datasets or experiments.
- A notebook, *Parsing arithmetic*, showcasing `grammar.proofnet` and
  `grammar.neural`: the two readings of `a + b * c` are two linkings of
  one sequent, 24 of its 120 linkings are correct, and a parser trained on
  formulae of up to four operators recovers `a + (b * c)`, and every one
  of 200 held-out formulae of five and six operators, in under a minute on
  a CPU.
- Closed terms are evaluated in a context, a list of distinct variables
  containing the free ones, through `closed.TermBase.weaken`, the structural
  morphism discarding the others and permuting the rest; `is_linear` says
  whether a term is, `compose` composes terms of function types,
  `occurrences` counts the free occurrences of a variable and
  `Substitution` is simultaneous and capture-avoiding, through the
  `substitute` method of each term, where it recursed forever on an
  abstraction.
  `closed.Ty.from_biclosed` and `closed.TermBase.from_biclosed` are
  functors dropping planarity, and `biclosed.Functor.map_term` sends a term
  to a term under a binding environment, checking the image against the
  image of its type and of its free variables
  ([#398](https://github.com/discopy/discopy/issues/398)).
- Products and let statements in the term language of `discopy.closed`:
  a not-strictly-associative `Product` type constructor called with `*`,
  `Pack`/`Unpack` boxes witnessing the isomorphism with the strict tensor,
  the `Tuple`, `Projection` and `Let` terms with a `let` introspection
  helper, and `Diagram.to_term` printing any causal diagram as a compact
  term in fine-grain call-by-value style via `Hypergraph`. The new terms
  are evaluated in a context through `weaken` like the others, substitute
  capture-avoidingly by renaming their bound variables, and say whether
  they are linear; `TermBase.share` is the structural morphism copying
  the free variables of a term into those of its subterms, which
  `Application`, `Tuple` and `Let` evaluate through. A closed constant
  prints as its bare name. `Tuple`, `Projection` and `Let` are `Compound`
  terms, equal when their parts are and printed only when their name is
  first read, so that `to_term` is linear rather than quadratic in the
  number of boxes ([#694](https://github.com/discopy/discopy/issues/694))
  ([#370](https://github.com/discopy/discopy/issues/370),
  [#458](https://github.com/discopy/discopy/issues/458),
  [#489](https://github.com/discopy/discopy/pull/489)).
- `traced.Sum`, `pivotal.Sum`, `compact.Sum` and `frobenius.Sum`, the formal
  sum of morphisms at the four levels of the hierarchy that had none, each
  mirroring its `Diagram`'s own bases and wired into `Diagram.sum_factory`.
  A functor with a formal sum in its codomain (e.g. `ar_map=lambda x: x + x`)
  crashed on any diagram in one of these four categories, unlike every other
  level ([#207](https://github.com/discopy/discopy/issues/207)).
- `CMap.is_scalar` is `not dom and not cod`, i.e. a scalar is an
  endomorphism of the unit, where it used to be "a single box with no ports,
  or a single scalar loop". Scalars are closed under tensor and that
  definition was not: a tensor of two scalar boxes has two boxes, so it
  answered `False`. `genus` keys its degenerate case on `n_vertices` rather
  than on this, since what Euler's formula cannot count is a map with no
  vertex to subdivide its loop, not a map with no boundary -- a closed map
  with many boxes is a scalar and still has a genus worth computing
  ([#690](https://github.com/discopy/discopy/pull/690)).
- `CMap.genus`, the number of handles of the smallest orientable surface a
  connected map embeds in, i.e. `(2 - χ) / 2`, deferring to
  `euler_characteristic` and raising with it on a map that is not connected.
  Zero for a map with no vertex, i.e. a loop, which is the one degenerate
  case: a circle does embed in the sphere, but Euler's formula only counts it
  once a vertex has subdivided it. A scalar is not degenerate — a standard
  combinatorial map is a connected scalar and has a genus like any other.
  `euler_characteristic` and `is_planar` were
  both here already, but a map that is not planar is not thereby all the
  same: the genus says *how far* from planar it is, which is the question
  asked by anything reading a topological obstruction off a map rather than
  just testing for one. `is_planar` is now "every component has genus zero"
  instead of repeating the scalar special case and the comparison against
  two ([#690](https://github.com/discopy/discopy/pull/690)).
- The style review keeps score. Every review it posts records the remarks
  it made, hidden in its own body, so the next round can read them back
  whole rather than parse its own prose. That next round is one request
  as before: the model is shown the past remarks with the replies they
  drew, alongside the revision it is reviewing, and says what became of
  each — `accepted` when the file now does what the remark asked,
  `declined` when someone answered that they would not do it, and neither
  while nobody has answered and nothing has moved. Each review then
  carries the tally of the remarks **it** made and no others, `3 style
  remarks: 1 accepted / 1 declined / 1 still open` — or `all accepted`, a
  state nothing is in being left out rather than counted at nought — so
  that a review says how what it asked for landed, read where it asked
  it. A round is scored by the ones that follow it, so the review being
  posted carries no tally yet and every round already posted is written
  again. A verdict that decided something survives a later round that
  forgets it: each tally carries the verdicts it recorded, hidden beside
  the line it shows, and a round merges its answers into them rather than
  recomputing the lot — a remark accepted while its file was in the diff stays
  accepted once the diff has moved on, where asking a model that can no
  longer see that file made the tally oscillate. A round is one review and
  says which round it is, so the reader sees how the review is landing
  without counting them. The prompt is ordered from what never moves to
  what moves every round — instructions, `STYLE.md`, context files, the
  past remarks as a list that only grows at its end, and last the revision
  under review — so that two rounds of one pull request share a prefix the
  gateway can serve from its cache rather than reading again
  ([#672](https://github.com/discopy/discopy/pull/672)).
- The style review never posts a review of a revision that is gone. Its
  concurrency group keyed on the event's action as well as the pull
  request, so a push cancelled the round another push had started but not
  one started by `ready_for_review` or by asking for it in a comment:
  those ran on, and posted a review of the head they had read minutes
  earlier, with line numbers belonging to a revision nobody could see any
  more. The group is now the pull request alone, so a newer trigger
  cancels the round in flight whatever started either of them, and
  `post.py` re-reads the head before posting and stands down when it has
  moved, leaving the review to the round that push starts. The base
  branch advancing is not this and never was: a merge base does not move
  when its target gains commits, so the diff both we and GitHub compute —
  and every line number in it — is the same before and after
  ([#672](https://github.com/discopy/discopy/pull/672)).
- The style review comments on the diff, and says where it could not.
  Whole files are what it reads to judge a change against the
  conventions around it, not an invitation to review code the change
  does not touch, so the prompt asks for findings on the lines the diff
  adds and says that going outside them is allowed but discouraged —
  for the case where what is wrong with a change is somewhere it did not
  touch. Every remark is a comment on the line it is about wherever
  GitHub takes one there, which is any line one of the diff's hunks
  shows; a remark further out goes in the review body, as do the ones
  past the ten-finding cap and, where GitHub refuses the inline comments
  outright, all of them. Left as a review of the file at large, the
  ten-finding cap went on code nobody was changing, and under the tally
  above those remarks stayed open forever, since fixing them was out of
  the pull request's scope
  ([#673](https://github.com/discopy/discopy/issues/673)). The body also
  names the changed files that did not fit one prompt — reviewed from
  their diff alone, or not reviewed at all — where that was said in the
  job's log and nowhere a reader would look, so a review with nothing to
  say about a file it never read whole read exactly like one that had
  read it.
- `monoidal.List`, the free monoid on a generator type: `List[X]` is a
  tuple of instances of `X` with concatenation as `tensor` and the empty
  list as unit, an `abc.Monoid` parameterised as
  `NamedGeneric["generator_factory"]` the way `Hypergraph[C]` is the
  hypergraph category over `C`. Free monoids come at three levels: `Ty`
  has arbitrary colours and generators, `List` a single colour and
  arbitrary generators, `Nat` a single colour and a single generator. A
  list is a sequence of its length-one sublists with the atoms as
  `inside`, and `abc.ColouredMonoid.cast` embeds a tuple of atoms, or a
  single atom, into any monoid. `List`, `Ty` and `hopf.Representation`
  hash by their fields rather than their `repr`, and `List.tensor` raises
  `TypeError` on anything but a list of the same type, `@` alone returning
  `NotImplemented` so that a list still whiskers a morphism on the left.
  `python.Function.ob` is `List[type]`
  rather than `tuple[type, ...]`: the `dom` and `cod` of a function are
  the free monoid on Python's `type`, a type or a tuple of types is cast
  into one wherever a function is built, indexing a function's `dom` or
  `cod` gives a list of length one and `dom.inside[i]` the type itself.
  `python.Ty` is an alias of `List[type]`, defined in `python.function`
  with `additive` and `multiplicative` re-exporting it; the package
  imports `multiplicative` on first use, since it imports `monoidal`
  which imports `python.finset`
  ([#728](https://github.com/discopy/discopy/issues/728)).
- `discopy/axioms.py`, a Hypothesis-based property-testing module, home
  of `Equation` (formerly `discopy.abc.Equation`): a law is stated once
  on `discopy.abc.Category` and every subclass inherits
  it, as an `Axiom` decorated with `@axiom`: a classmethod of its
  category — the class it is bound to — implicitly, its remaining
  parameters generated from their annotations, `C0`, `C1` or `Self` for
  the objects, arrows or terms of the category;
  `.failing`/`.inapplicable` classify a
  law as broken or not applicable to a category, and `.modulo`/`.weaken`
  are defined (compare up to a function, quantify over a named subspace)
  but not used yet. A
  broken law raises `AxiomFailure` carrying its equation, whose sides say
  how it failed; `Axiom` is a dataclass whose classifiers derive one from another
  with `dataclasses.replace`, so none of them drops a field — `.failing`
  used to lose the subspaces a `.weaken` declared. The argument and
  subspace wrappers are parameterised with `NamedGeneric["factory"]` like
  `Hypergraph` and `Equation` — which moves `NamedGeneric` itself down to
  `discopy.utils`, re-exported from `discopy.abc`, so `discopy.axioms`
  can use it — making a subscripted wrapper a class whose
  `strategy(cls, **params)` matches the contract `Testable.strategy` now
  states, so a subspace annotation like `ComposablePair[C1]`
  builds; an unbound axiom's `.strategy()` raises the same `TypeError`
  as `.falsify` and calling it. The
  search itself is the canonical instantiation only — one atomic object or
  one free/generator box per parameter, no recursive or compound
  generation — wired up in `proptest/test_axioms.py`, enrolled so far for
  `cat.Arrow`, and run by the new `proptest` GitHub
  workflow on PRs labelled `proptest`, on `main`, nightly and on manual
  dispatch. `proptest/conftest.py` registers four Hypothesis profiles
  over one example database, keyed per cell: `pr` replays what the
  database remembers and generates a few examples from a fixed seed,
  `explore` searches with a large budget, `dev` works on the local
  database alone and `shared`, registered only when selected, backs it
  with CI's through a read-only `GitHubArtifactDatabase` and a
  `GITHUB_TOKEN`. The workflow downloads the database from the previous
  run's artifact, and a run of `main`, the nightly search or a dispatch
  uploads its own afterwards — a pull request only reads it — so a
  counterexample found by one night's search fails every pull request
  until it is fixed or declared, and `Axiom.falsify` searches for one on
  demand. `Testable`
  states the laws of any type that generates its own instances, whatever
  its level: `transparency`, `pickling` and `serialisation` are cells of
  the matrix for every category — `eval(repr(x))`, the pickle and the tree
  of a term read back to it, as `Equation`s like every other law — with
  `Testable.environment` for the namespace a representation reads back
  in — the package's public names and then those of the module the
  category is defined in, so that a term printing bare names such as
  `Tensor[int]([0], dom=Dim(1), cod=Dim(1))` reads back without its
  category declaring anything; the ad-hoc property
  files for representations, pickling and serialisation are gone, and a
  known violation is a `.failing` declaration on its category like any
  other broken law. `discopy.axioms` joins the API docs under its own
  `axioms` page, with `CONTRIBUTING.md` saying how to run the suite;
  `AGENTS.md` points to it from `Where` rather than importing it into
  every agent's context.
- `abc.Nat`, a concrete dataclass for the free monoid on one generator
  (`n: int` with addition as `tensor`), and `abc.PRO`/`abc.PROB`/`abc.PROP`,
  the `MonoidalCategory`/`BraidedCategory`/`SymmetricCategory` whose objects
  are `Nat` — `PROB(PRO, BraidedCategory[Nat, C1])` and
  `PROP(PROB, SymmetricCategory[Nat, C1])`, mirroring how
  `abc.SymmetricCategory` already extends `abc.BraidedCategory` directly.
  `abc.Nat` also gets `__index__` (so `range(n)`/`int(n)` work whether `n`
  is a plain `int` or a `Nat`) and its `tensor` now returns `NotImplemented`
  for a non-`Nat` argument, like `monoidal.Ty.tensor` already does
  — needed to let `@` fall back to the other operand's `__rmatmul__` for
  whiskering, e.g. `Nat(1) @ some_morphism`, which previously crashed with
  `AttributeError` instead of building the identity on `Nat(1)` first.
  `python.finset.Function`/`Permutation.ob` changes from a raw `int` to
  `Nat`, its `dom`/`cod` now genuinely `Nat` instances (auto-cast from `int`
  at construction, the same convenience `monoidal.Diagram` already gives
  any `ob = Nat` subclass) rather than merely claiming to be one without
  the objects to match; `Permutation` inherits `abc.PROP` on the strength
  of that, its first genuine user
  ([#709](https://github.com/discopy/discopy/issues/709)).
- Monoidal lenses, also called optics, `discopy.lens`, with one class for
  each doctrine of the underlying category as in `discopy.para`.
  `lens.Symmetric` is a residual with a forward and a backward morphism
  over a symmetric category, composing by tensoring the residuals as
  `discopy.para` does with its co/parameters, over pairs `lens.Ty`
  tensored componentwise; `to_int` reads one over a traced category as an
  integer diagram of `discopy.interaction`, the residual being the wire
  between the legs, and `lens.Traced` traces it leg by leg.
  `lens.Markov` is the lenses of functional programming, a `get` and a
  `put` composing by the chain rule over a Markov category: a subclass of
  `lens.Symmetric` whose residual is the input, copied to be read by `get`
  and kept for `put`, and `lens.Symmetric.to_markov` normalises any lens
  to one. Lenses over
  `python.Function` are the reverse derivatives of gradient-based
  learning, and a parametric lens `para.Symmetric[lens.Markov[Function]]`
  a neural network with its weights' gradients beside its input's.
  Building a Markov lens over a category without `copy` and `discard`
  raises `messages.NOT_MARKOV`
  ([#701](https://github.com/discopy/discopy/pull/701)).
- A `workflows` job in `build.yml`, so that the code running our pull
  requests is checked like the code it checks: `actionlint` over the
  workflows, `pflake8` over `.github`, and `pytest .github/tests/*.py`
  over the three scripts and the composite action, whose steps take a
  strict subset of a workflow step's keys that `actionlint` does not
  check. Three of the last five changes to `.github`
  were fixing bugs in `.github`
  ([#611](https://github.com/discopy/discopy/issues/611),
  [#615](https://github.com/discopy/discopy/issues/615),
  [#640](https://github.com/discopy/discopy/issues/640)), every one found
  in production. On its first runs shellcheck found the `A && B || C` in
  `benchmark.yml`'s summary step, now an `if`
  ([#645](https://github.com/discopy/discopy/pull/645)).
- `.github/actions/setup`, one composite action for installing uv, Python,
  the project and, for the jobs that draw, Graphviz. The three `build.yml`
  jobs called for it four times between them and the Graphviz incantation
  was byte-identical twice. `benchmark.yml` keeps its own steps: it checks
  out two arbitrary commits and one of them predates this action
  ([#645](https://github.com/discopy/discopy/pull/645)).
- `.github/dependabot.yml`, grouping the monthly GitHub Actions updates
  into one pull request, now that every action is pinned by commit
  ([#645](https://github.com/discopy/discopy/pull/645)).
- `Diagram.to_compact` and `CMap.to_compact`, bending curry bubbles into
  coevaluation and feedback. Since a biclosed category has no trace, the
  `biclosed` method lands in `CMap`, which is compact whatever hosts it,
  while the `closed` one stays in diagrams. Unlike `rigid.to_rigid` and
  `interaction.Int`, this keeps the exponential atomic and bends the wire
  with `biclosed.Coeval`, the transpose of `Eval`, which a biclosed
  category only has when its exponential is read at a reflexive object
  ([#532](https://github.com/discopy/discopy/pull/532)).
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
- Quantum reservoir computing, `discopy.quantum.reservoir`: a `Reservoir`
  is a fixed unitary on memory and input qubits, each input value induces
  a channel from memory to memory, the features of a time series are the
  Born probabilities of the memory qubits and only a ridge-regression
  linear readout is trained, with a `Rydberg` reservoir as example
  ([#519](https://github.com/discopy/discopy/pull/519),
  [#586](https://github.com/discopy/discopy/pull/586)).
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
- `discopy.kleisli`, the Kleisli category of a `Monad`, with the channel,
  multiplicative and additive instances. `Monad` carries an optional
  `iterate` operator, i.e. the structure of an Elgot monad, so that
  `kleisli.additive.Channel.trace` is defined exactly for the monads that
  supply one, with Dal Lago-Hoshino's token machines as a worked example
  where conditioning is a trace. `kleisli.additive.Channel` declares itself
  a `TracedCategory`, so whiskering on either side comes from
  `MonoidalCategory`. `python.function.EndoFunctor`, which `Monad`
  extends, sends lists of types to lists of types since `Function.ob` is
  `List[type]` ([#728](https://github.com/discopy/discopy/issues/728)):
  `Maybe(int) == Ty(int | None)`, and the `dom` and `cod` of an additive
  or multiplicative channel are lists of types, cast from a tuple
  ([#443](https://github.com/discopy/discopy/pull/443)).
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
- `Rydberg` in `discopy.quantum.ansatze`, the Trotterized time evolution
  under the Rydberg Hamiltonian of Pasqal's neutral-atom QPU
  ([#586](https://github.com/discopy/discopy/pull/586)).
- The pivotal structure of `Rep(H)`: `HopfAlgebra.drinfeld_element`,
  `pivotal_element` and `ribbon_element`, cached single tensors named after
  the literature (Reshetikhin–Turaev; Kassel; Radford), with pivotal cups
  and caps twisting the dual leg so all four orientations are intertwiners.
  `taft(n)`, the smallest algebras with a pivot of order `n` (Sweedler's
  algebra is `n = 2`), realise the Kauffman–Radford ribbon criterion
  ([#484](https://github.com/discopy/discopy/pull/484)).
- Syntactic beta reduction on `closed.Term` with capture-avoiding
  substitution, and `closed.BohmTree` as the normal form: its arguments are
  reduced lazily against a shared budget, with pluggable reduction
  strategies defaulting to leftmost-outermost
  ([#442](https://github.com/discopy/discopy/pull/442)).

### Changed

- `Equation` has one symbol fewer than terms, a symbol between each pair of
  consecutive terms, where it stored one per term; `symbols` of any other
  length raise `ValueError`
  ([rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1)).
- A property read off a value with `hasattr` is read with `isinstance`
  where a class states it: adjoints by `Pregroup`, swaps by
  `SymmetricCategory`, identities by `Category`, windings by a
  `rigid.Box.z` of zero by default, arrays by `tensor.Box`, a list of
  numbers by `Sized` and a file by not being a path. A
  `MappingOrCallable` is a mapping when it wraps a `Mapping` and a
  callable when it wraps a callable, where anything indexable was a
  mapping, and it raises `TypeError` on anything else as soon as it is
  built rather than on its first lookup. `interaction.Ty` is a
  `Pregroup`, as its negation is both its adjoints, and
  `assert_isadjoint` moves from `rigid.Ty` to `Pregroup`, beside
  `is_adjoint`, so that integer types check their cups and caps as rigid
  ones do; `x << y` and `x >> y` are their exponentials. A functor still
  asks its codomain for structure by name, as a `Hypergraph`, a
  `Stream`, a `Matrix` or a `Tensor` has more than the abstract class it
  subclasses states
  ([rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1)).
- A class subscripted with a DisCoPy class is named by its `factory_name`,
  e.g. `hypergraph.Hypergraph[frobenius.Diagram]` rather than
  `Hypergraph[Diagram]`, since every level of the hierarchy has a `Diagram`
  of its own; a parameter that is not a class, e.g. the algebra of a
  `hopf.Representation`, is named as before
  ([rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1)).
- `Hypergraph.to_diagram` and `CMap.to_diagram` route the wires of each
  box with one permutation rather than a staircase of swaps: the domain
  wires of the box are gathered at its offset, the other wires keeping
  their order, by the new `finset.Permutation.gather`, and the permutation
  is emitted once through the new `abc.SymmetricCategory.from_permutation`,
  which `symmetric.Diagram.from_permutation` overrides with a native
  `Permutation` box and which defers to `permutation` in a concrete
  category, a composition of swaps by default and a single array in
  `Tensor`; the final alignment with the codomain is one permutation too.
  Since `symmetric.Layer` coalesces
  plumbing, each swap of the staircase was already a full-width
  `Permutation` layer, so a routing step of `n` swaps was `n` layers and
  is now one: `simplify`, `foliation` and `from_callable` give shorter
  diagrams, a permutation round-trips to itself,
  `Diagram.permutation([2, 0, 1], x @ y @ z).simplify()` being
  `Permutation(x @ y @ z, [2, 0, 1])`, and a decoded diagram never has two
  consecutive layers of plumbing. The one baseline this redraws is
  `symmetric/decorator.svg`, whose two staircases of swaps become one
  band of crossing wires each
  ([#539](https://github.com/discopy/discopy/issues/539),
  [#546](https://github.com/discopy/discopy/pull/546)).
- `monoidal.Colour` is transparent by default rather than white, i.e. its
  `name` defaults to the new `config.TRANSPARENT` and `monoidal.white` is
  renamed to `monoidal.transparent`. The drawing code painted every region
  but skipped the white ones, so the neutral background was spelt "white"
  and a white region could not be asked for: the region was not filled, it
  was left out of the legend, the wires around it adapted to a dark page as
  if they lay on the bare canvas and a spider coloured white was drawn
  unfilled. Each of those now tests for the transparent colour, so white is
  a colour like any other and the neutral background is the one that is
  actually transparent, as `savefig` already made the canvas
  ([#751](https://github.com/discopy/discopy/issues/751), completing
  [#725](https://github.com/discopy/discopy/pull/725) with what
  [#497](https://github.com/discopy/discopy/pull/497) had right). Nothing
  in the library asks for a white region, so the drawings are unchanged:
  the symbol of an `Equation` and the slots around its terms are
  transparent now rather than white. The one exception is TikZ, which
  spelt the symbol `fill=white` where matplotlib already drew it unfilled
  and now agrees with it, `TikZ.format_color` passing the transparent
  colour through as TikZ spells it the same way.
- `monoidal.Ty` is the free coloured monoid itself: it subclasses
  `cat.Ob`, `cat.FreeCategory` and `abc.ColouredMonoid` directly, folding
  in the unreleased `FreeMonoid` whose only subclass it was. Addition is
  no longer an alias of the tensor on any object: `Ty.__add__`,
  `stream.Ty.__add__` and `interaction.Ty.__add__` are removed, `+` raises
  `TypeError` on a `List`, and every fold of objects with `sum` or `+` — in
  `abc.SymmetricCategory.permutation`, `Hypergraph.from_graph`,
  `interaction.Ty.tensor`, `stream.Ty.sequence` and `para` — goes through
  `tensor`. `matrix.Matrix.ob` is `abc.Nat` rather than a bare `int`, its
  `dom` and `cod` cast from `int` at construction as `python.finset` already
  does ([#709](https://github.com/discopy/discopy/issues/709)): the
  `Int`-construction over `Matrix[bool]` folds its objects with `tensor`,
  which an `int` does not have, and `abc.Nat` prints as its number so a
  matrix still reads `dom=2, cod=2`. `para.Symmetric` checks that its four
  objects are `category.ob`, so a tuple of types is refused where it used
  to be concatenated with `+`
  ([#750](https://github.com/discopy/discopy/issues/750)).
  `monoidal.Functor` folds the images of every object with `tensor` instead
  of the `+` it fell back to while `python.Function.ob` was a bare tuple,
  and `_map_atomic` goes with the tuple case it existed for, as do the
  tuple special case of `stream.Ty` and `utils.is_tuple`
  ([#728](https://github.com/discopy/discopy/issues/728)).
- `monoidal.PRO` (and its counterparts `rigid.PRO`, `pivotal.PRO` and
  `frobenius.PRO`) is renamed to `Nat`: it is the free monoid on one
  generator, natural numbers with addition as tensor, and its unary
  encoding was already exposed through the sequence protocol
  (`len`, iteration and slicing, e.g. `Nat(3)[:1] == Nat(1)`), just under
  the wrong name — `PRO` is the name for the monoidal category with `Nat`
  as objects, see `abc.PRO` above. `abc.Nat` carries the concrete
  behaviour (its dataclass field `n`, `tensor` as addition, the sequence
  protocol), so `monoidal.Nat` only adds what a `Ty` needs on top: `dom`,
  `cod`, `inside`, serialisation and the whiskering-aware `tensor` that
  raises on a mismatched `Ty` rather than silently reinterpreting it.
  `monoidal.Functor.__call__` maps a `Nat` by mapping its single generator
  once and folding that image `other.n` times with `@`, rather than mapping
  each of the `n` identical atoms separately: a `Nat` is a unary encoding,
  so every atom is the same generator and its image need only be computed
  once. The fold starts from the image's own unit (`image[:0]`) rather than
  the declared codomain unit `cod.ob()`, since the latter can be a supertype
  of the image — `Diagram.to_hypergraph` on a `Nat`-typed permutation maps a
  `Nat` boundary through a functor whose `cod.ob` is the category's generic
  `Ty`, and `Ty() @ Nat` is refused. The old names still work
  through a `DeprecationWarning`, via a new `utils.deprecated_alias` taking a
  mapping of every name a module deprecates. `utils.deprecated_ob`, the
  single-purpose `Ob`→`Wire` wrapper it generalises, is removed: its six call
  sites (`biclosed`, `braided`, `compact`, `feedback`, `grammar.pregroup`,
  `quantum.circuit`) now call `deprecated_alias(__name__, {"Ob": "Wire"})`
  directly, the same as `rigid`/`pivotal`/`frobenius`/`monoidal` already do
  for their `PRO`→`Nat` alias
  ([#709](https://github.com/discopy/discopy/issues/709)).
- Matplotlib SVGs adapt to the page behind them: they are saved on a
  transparent canvas and open with a `prefers-color-scheme: dark` media
  query that turns the elements drawn black on that canvas — wires, braids,
  wire labels, spiders and their labels, control dots — white on a dark
  page, so a single SVG file reads on both light and dark backgrounds.
  Elements whose readability does not depend on the page keep their static
  colours: box interiors stay white with black labels, coloured regions
  keep their fill and the black strokes over them. White spiders, e.g. the
  symbol of an `Equation`, are drawn unfilled so they leave no white patch
  on a non-white page, and raster formats keep their white background since
  they cannot adapt. The docs let content images follow the theme toggle by
  setting their `color-scheme`, which propagates into the SVG media query,
  instead of painting a white plate behind them in dark mode
  ([#453](https://github.com/discopy/discopy/issues/453), superseding the
  static outlines of
  [#497](https://github.com/discopy/discopy/pull/497)). The hand-drawn
  snake equation of the README header adapts the same way, replacing its
  separate `snake-equation-dark.svg`, and the unreferenced
  `frobenius-axioms.svg` is deleted.
- The benchmark measures a pull request against its merge base rather
  than the tip of its base branch. The head does not contain what landed
  on `main` since it forked, so measuring against the tip charged the pull
  request for everyone else's commits. `benchmark.yml` resolves it with one
  `compare` call and records it as `previous` in the artifact metadata,
  next to the `base` the comment still validates itself against
  ([#645](https://github.com/discopy/discopy/pull/645)).
- `benchmark-comment.yml` is 33 lines of YAML calling
  `.github/scripts/benchmark_comment.py` rather than 140 lines of
  JavaScript embedded in YAML. Nothing needed `actions/github-script`: the
  event payload is a JSON file named by `GITHUB_EVENT_PATH` and the REST
  API is `urllib`, from the standard library.
  In Python it is lintable, testable and in the one language this
  repository is written in; its validation is `unreadable`, `unattested`
  and `mismatch`, three pure functions the tests state the refusals of.
  The job also stopped taking the artifact's word for three things, since
  the pull request can write it: the pull request number is checked to be
  an integer before it reaches a URL rather than after, the merge base the
  comment links is checked against one the job computes itself from two
  commits it already trusts, and a run that lists no pull request of its
  own -- one from a fork -- must name the single open pull request for its
  head rather than any that shares its branch. A download that fails is no
  longer silence: the job asks whether the artifact was staged at all, and
  only then posts nothing
  ([#645](https://github.com/discopy/discopy/pull/645)).
- `build.yml` and `benchmark.yml` cancel a pull request's superseded runs
  but let every commit on `main` finish, `cancel-in-progress` reading
  `github.event_name == 'pull_request'`. Cancelling on `main` left commits
  nothing ever built — `112b6036` is one — and threw away the pair of
  measurements a benchmark run exists to produce
  ([#645](https://github.com/discopy/discopy/pull/645)).
- Every action is pinned by commit, not by moving tag, as
  `benchmark-comment.yml` already pinned two of them; `build.yml` declares
  `permissions: contents: read` like the other four workflows; and every
  checkout sets `persist-credentials: false`
  ([#645](https://github.com/discopy/discopy/pull/645)).
- `build.yml` drops the `SRC_DIR` and `TEST_DIR` variables, which nothing
  read, and the `tooling/uv-migration` push trigger, whose branch is gone
  ([#645](https://github.com/discopy/discopy/pull/645)).

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
- `Sqrt` of a negative or complex number carries an `is_dagger` flag that
  conjugates its array, so such a square root and its dagger are no longer
  equal; a real square root stays self-adjoint and rejects the flag
  ([#482](https://github.com/discopy/discopy/issues/482)).
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

### Removed

- Parameters nothing read: `grammar.cfg.Tree.to_diagram`'s
  `contravariant`, a placeholder since the module's first commit;
  `Tree.from_nltk`'s `lexicalised` and `word_types`, which the grammar
  refactor stopped reading; `Drawing.id`'s `length`;
  `markov.Diagram.discard`'s `n`; and `drawing.backend.Backend`'s
  `linewidth` ([#768](https://github.com/discopy/discopy/pull/768)).
- `cat.Bubble.dagger`: a bubble's dagger was inherited from `Box.dagger`,
  which reconstructs with `type(self)(name, cod, dom, ...)` — positional
  arguments `Bubble.__init__` reads as `*args`, so it crashed with
  `AttributeError` on the very first (non-arrow) argument. `Bubble` now
  daggers each of its `args`, swaps `dom`/`cod` and carries `data`/`is_dagger`
  through like `Box.dagger` does
  ([#55](https://github.com/discopy/discopy/issues/55)).
- `style-review.yml`'s hand-over to the correctness reviewer, and its
  token generation, ran on every style review rather than the intended
  ones. Both conditions were written as `if: >` folding a wrapped
  `${{ ... }}` into a string with a trailing newline: with characters
  around it the expression is no longer the whole value, so GitHub read a
  non-empty string and took it as true. `@cubic-dev-ai review` was
  therefore posted whatever the style review found, where it is meant to
  wait for a clean one. [#634](https://github.com/discopy/discopy/pull/634)
  rewrote both conditions and the shape survived, so the fix is applied to
  its versions: written bare, as the file's other five conditions are
  ([#645](https://github.com/discopy/discopy/pull/645)).
- The in-house style reviewer — `.github/style-review/` (the `review.py`,
  `post.py`, `history.py`, `thread.py` and `github.py` scripts and their
  `prompt.md`), the `style-review.yml` workflow, and their tests under
  `.github/tests/` — is retired in favour of CodeRabbit, configured by a
  new `.coderabbit.yaml` that restates `STYLE.md` as per-path review
  instructions. It was built around our own open-weights model behind an
  OpenAI-compatible gateway, and around a cross-round `accepted`/`declined`/
  `open` tally kept in hidden review bodies; CodeRabbit is free for public
  repositories, so the gateway (and the `STYLE_REVIEW_BASE_URL`/`_MODEL`
  variables and `STYLE_REVIEW_API_KEY` secret it read) is no longer needed.
  Correctness review is unchanged — cubic keeps that lane — but the two
  reviewers now run as independent GitHub Apps on pull request events, so
  the style→correctness hand-over the workflow orchestrated (the source of
  #634/#645/#676) is gone rather than reimplemented. The `no-todo-on-main`
  draft gate stays: a draft carries its `TODO.md` and CodeRabbit skips
  drafts, so deleting `TODO.md` still hands a pull request to the style
  reviewer first.

### Fixed

- An exponential of the unit is its base, `x << Ty()`, `Ty() >> x` and
  `x ** Ty()` being `x` on biclosed and closed types, so that `curry(0)` is
  the identity and the evaluation at the unit is too: a curry of no wire
  was a box into `Ty() << Ty()`, which `to_map` crashed on. A curry
  refuses its dagger with an `AxiomError`, where it crashed calling its
  constructor with the arguments of a box, and `biclosed.Curry.to_drawing`
  traces the `n` wires it curries, where it traced one whatever `n` was
  ([rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1)).
- A binary term or type raising of a categorial grammar evaluates with a
  functor passed positionally, as the terms around it pass it, where
  `FX(FC(a, b), r).eval()` raised `TypeError`; the categorial grammar has a
  `Coeval`, so that the dagger of its evaluations stays in its category;
  and `grammar.categorial.Diagram` and `grammar.abstract.Diagram` bind
  their own `box_factory`
  ([rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1)).
- `Stream.sequence` builds the boxes of the category the stream is over,
  where it built `symmetric.Box` whatever the category; `para.Closed.curry`
  defaults to `left=True` like every other curry since #560; decoding with
  neither boxes and offsets nor their zip, and subscripting a
  `NamedGeneric` that has no type parameter, raise with a message; and the
  recipe of the `diagrams` notebook sets `ob`, where it set a `ty_factory`
  nothing reads
  ([rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1)).
- `Diagram.foliation` is idempotent. A diagram records the offsets of its
  states whenever it has one, where it did only when each layer held one
  box, so a foliated diagram with several states in a layer refoliated
  differently; and the foliation read off a hypergraph merges its layers,
  so consecutive permutations compose into one. `rigid.Diagram.snake_removal`
  loses a guard on an attribute no layer has, which raised a message that
  did not exist
  ([rel-int/discopy-next#1](https://github.com/rel-int/discopy-next/pull/1)).
- `Matrix.copy(x, n)` is the diagonal of the direct sum, `n` identities
  side by side, i.e. `array[i, j]` iff `j % x == i`, where it was the
  Kronecker diagonal, the copy of the tensor product: under the direct sum
  it was neither cocommutative nor counital, and at `x = 3` its middle row
  was empty, so it was not even a function. `copy` and `permutation` build
  their array in the `dtype` of their carrier, `int` by default like `id`
  and `zero`, where a list of booleans inferred `bool` and an empty one
  `float64`, so that `discard(x)`, `swap(0, 0)` and `permutation([], [])`
  compose with the structural matrices without promoting them; `merge`
  defaults to two copies like `copy`. `Tensor.copy` is the spider of the
  Kronecker product, as it was. The laws of a commutative comonoid --
  coassociativity, cocommutativity, counitality -- and the coherence of
  `copy` with the tensor are stated once on `abc.MarkovCategory`, which
  gains `discard` as `copy(x, 0)`, and hold on both carriers; a term being
  a box, they are inapplicable to `closed.TermBase` like the laws of its
  diagram category. `Matrix[int]` joins the property matrix with a
  `strategy` of small integer matrices, its `serialisation` inapplicable
  (`messages.NO_SYNTAX`), and `abc.Nat` is `Testable` with a `strategy` of
  its own, since the search asks `Matrix.ob` for one. Fixed upstream the
  same way by nightmare6728's
  [#795](https://github.com/discopy/discopy/pull/795)
  ([#652](https://github.com/discopy/discopy/issues/652),
  [rel-int/discopy-next#80](https://github.com/rel-int/discopy-next/issues/80)).
- `Tensor.then(g, h)` with several arguments folds `Tensor.then`, where it
  folded `Matrix.then`: `utils.unbiased` applied the function it decorated
  to every pair, so the n-ary case of a subclass overriding the binary one
  -- `Tensor`, and `Channel` through it -- ran the parent's `numpy.matmul`
  on arrays of several axes, batched over the leading ones: wrong entries
  on compound dimensions, silently, and `ValueError` on unequal ones. The
  fold now calls the method by name on the running result, one argument
  being its base case, so that it is the binary composition of whatever
  class the result is, and `Tensor.then()` with no argument is the
  identity as `Matrix.then()` was, where it raised `TypeError`
  ([rel-int/discopy-next#60](https://github.com/rel-int/discopy-next/issues/60)).
- `Tensor[complex].ar is Tensor[complex]`, and likewise for the subscripts
  of `Matrix`, `Channel` and every `NamedGeneric` class that is its own
  `factory`: `@factory` sets `factory` on the class it decorates and a
  subscript inherited it, so `symmetric.Functor` built swaps and
  permutations with the unparameterised `Tensor`, whose `id` is `int64`,
  and `Swap[complex](Dim(2), Dim(3)).eval()`, or a functor with
  `dtype=complex` on a swap or a permutation, came out `Tensor[int64]`. A
  subscript of a class that is not a factory, `Hypergraph[C]` or `CMap[C]`,
  keeps its `ar` as itself
  ([rel-int/discopy-next#77](https://github.com/rel-int/discopy-next/issues/77)).
- `python.Function.trace` evaluates, and builds for `n > 1`. `fix` seeded
  its iteration by calling the function without its traced argument, so
  that the default of a lambda's last parameter was the initial value: the
  composite that `trace` iterates could not pass it on, since `__call__`
  rejects the arity before the lambda is reached and a missing argument
  cannot be routed through a swap, so every trace raised `ValueError` when
  called; and `trace(n)` took its fixed point over one type whatever `n`,
  so `trace(2)` raised `AxiomError`. The iteration now starts from the
  default instance `t()` of each traced type `t`, e.g. `0` for `int`, a
  value that type checks and flows through any composite, and stops when
  two iterates are equal; `fix(n)` takes the fixed point over the last `n`
  types at once and checks that they are the codomain, `trace` checks that
  it is traceable, and both evaluate through `__call__` rather than around
  it. The laws of traced categories hold on feedback with a unique fixed
  point, and an integer diagram over `Function` evaluates, e.g. the chain
  rule of two reverse-mode squares composed in `Int(Function)`. The golden
  ratio of the examples notebook and of the `traced.Functor` docstring is
  the fixed point of `x -> sqrt(1 + x)` from zero, with the type checking on,
  where both used to read the default `x=1` of a lambda with it switched off,
  and `traced/golden.svg` is redrawn with the new label. Both refuse an `n`
  below zero or past the types they have, where the slices wrapped around.
  `test_trace` never called the trace it named
  (B87 of [#31](https://github.com/rel-int/discopy-next/issues/31))
  ([rel-int/discopy-next#73](https://github.com/rel-int/discopy-next/issues/73)).
- `rigid.Nat.unwind` is the identity, like its `l` and `r`: `rigid.Ty.unwind`
  asks the atom of a type for its winding and the atoms of a `Nat` are
  integers, so `Hypergraph.__init__` raised `AttributeError` on any
  `Nat`-typed diagram and nothing going through `to_hypergraph` worked on a
  ZX diagram, neither `simplify` nor `frobenius.Equation`
  ([rel-int/discopy-next#76](https://github.com/rel-int/discopy-next/issues/76)).
- `zx.Diagram.to_pyzx` keeps parallel wires: a pyzx graph is simple and a
  second wire between the same two spiders overwrote the first, so
  `to_pyzx().to_matrix()` disagreed with `eval()` on
  `X(1, 2, .75) >> Z(2, 1, 1 / 3)`; the wires into each spider now go
  through pyzx's `add_edge_table`, which merges them by the fusion and Hopf
  rules with their scalars in `graph.scalar`. A `Y` spider was sent to an X
  vertex, so `Y(1, 1, .5)` read as the Pauli X: pyzx has no Y vertex, so
  `Y.to_x` encodes it, exactly for every arity and phase, as an X spider
  with the phase gate `S = Z(1, 1, .25)` on each leg out and its dagger on
  each leg in, since the eigenbasis of Y is `S` applied to the Hadamard
  basis
  ([rel-int/discopy-next#74](https://github.com/rel-int/discopy-next/issues/74)).
- `zx.Spider.grad` is the derivative of the standard interpretation: it used
  the formula of `gates.Rotation.grad`, `pi * Z(n, m, a + .5)`, right for
  `Rz(a) = diag(exp(-i pi a), exp(i pi a))` but not for a spider, which is
  `diag(1, exp(2 pi i a))` on its legs and whose derivative is the formal
  sum `i pi (Z(n, m, a) - Z(n, m, a + .5))` of arXiv:2103.07960, built
  through `sum_factory` and checked against finite differences
  ([rel-int/discopy-next#75](https://github.com/rel-int/discopy-next/issues/75)).
- The Dal Lago & Hoshino citation in `kleisli.additive` pointed at
  arXiv:1904.11324, which is not their paper; the geometry of Bayesian
  programming is arXiv:1904.07425
  ([#639](https://github.com/discopy/discopy/pull/639)).
- `interaction.Diagram.trace` traces an integer diagram, where it raised
  `TypeError` on every input: it was borrowed from `traced.Diagram` through
  a `trace_factory` slicing the type, and an integer type is a pair of
  types rather than a sequence of atoms, since positive and negative atoms
  commute. The trace over a pair `(u, u_)` is the natural trace of the
  inside over both halves at once, after the braids that bring them side
  by side, and it agrees with the feedback loop made of cups and caps up
  to the axioms of traced categories: on the nose over `Matrix[bool]`, by
  hypergraph over symmetric diagrams, and with the trace of `lens.Traced`
  through `to_int`. Its `n` counts atoms on each half, or one number per
  half, read off the type by the new `interaction.Ty.split`, which also
  gives `curry` and `uncurry`, borrowed stubs that sliced the type the
  same way, and `twist` is the trace of the braid, as in `ribbon`.
  `Int` of a symmetric category needs neither a dagger nor a twist:
  `then`, `tensor` and `braid` took the inverse braid as the dagger of the
  braid and `id` the natural twist, so `Int(python.Function)` could be
  built but neither composed nor compared with an identity; the new
  `natural_braid` and `natural_twist` read the braid the other way around
  and the identity when `is_symmetric`, and keep the dagger path for
  balanced categories. `rotate`, `l` and `r` are the transpose, since an
  integer diagram has no box to rotate, which is what the borrowed
  `conjugate` was missing
  ([#732](https://github.com/discopy/discopy/issues/732)).
- Every `NamedGeneric`-parameterised class pickles with its parameter.
  `NamedGeneric`
  encodes a member of `L[v]` as a member of `L` carrying `v` in its state,
  to be read back by a `__setstate__` it defined on `NamedGeneric` itself,
  which no class built from `NamedGeneric[...]` inherits: so
  `interaction.Ty[int]`, `Hypergraph[D]`, `List[int]`, `Matrix[int]`,
  `Tensor[complex]` and `CMap[D]` all came back from `pickle.loads` and
  `copy.deepcopy` with the parameter `None` and the values left in their
  `__dict__`, and `pickle.dumps` wrote them into the live object's
  `__dict__` on the way, since it merged them into the state in place.
  The decoding half is defined on the class every `NamedGeneric[...]`
  subclass inherits, restoring the rest of the state through the next
  `__setstate__` of the hierarchy, and the encoding half copies the state;
  `tensor.Box` no longer calls the former by hand
  ([#749](https://github.com/discopy/discopy/issues/749)).
- `biclosed.Variable`, `Application` and `Abstraction` read back from
  their tree, and with them the `closed`, `grammar.abstract` and
  `grammar.categorial` terms built on them, the type raisings and the
  binary compositions: every one inherited `Box.from_tree`, which rebuilds
  with the `name`, `dom` and `cod` keywords their constructors do not take,
  so `loads(dumps(term))` raised `TypeError` on any term but a constant.
  `serialisation` is a law of `biclosed.TermBase` and `closed.TermBase` in
  the property matrix again, where it was declared failing
  ([#692](https://github.com/discopy/discopy/issues/692)).
- `monoidal.Bubble` keeps the `data` and `is_dagger` it is built with: its
  constructor called `Box.__init__` a second time with the name and the
  boundary alone, after `cat.Bubble.__init__` had set them, so
  `f.bubble(data=42).data` was `None` and the dagger of a bubble was not
  marked as one. The tree of a `cat.Bubble` carries both as the tree of a
  box does, and its `name` and `method` when they are not the defaults, so
  all four survive `loads(dumps(...))` too
  ([#637](https://github.com/discopy/discopy/issues/637)).
- `tensor.Dim` reads back from its tree. It used to inherit `Ty.to_tree`,
  which asks each atom for its tree where a dimension has plain integers
  inside, so `dumps(Dim(2, 3))` raised `AttributeError`; `monoidal.Dim`,
  the base of `frobenius.Dim` and so of `tensor.Dim`, keeps the integers
  in its tree since [#736](https://github.com/discopy/discopy/pull/736),
  and a regression test pins it
  ([#681](https://github.com/discopy/discopy/issues/681)).
- `zx.Diagram.eval` is the standard qubit interpretation, where it silently
  returned wrong tensors: `Z(1, 1, 0.5).eval()` was a scalar on `Dim(1)` and
  `H.eval().array` was `nan`, since the atoms of `Nat` are the integer `1`
  with no `dim`, and a composite diagram crashed in `to_map`.
  `tensor.Diagram.dim` is the object map of `eval`, `to_quimb`, `to_tn` and
  of the arrays of `Box` and `Permutation` -- the `dim` of each atom --
  which `zx.Diagram` overrides with `Dim(2)` per wire; `zx.Spider.array` is
  the phased spider in the eigenbasis of its colour, `Spider.basis`, so that
  `Z(1, 1, .5)`, `X(1, 1, .5)` and `Y(1, 1, .5)` are the three Paulis and
  `X(n, m, a)` is `Z(n, m, a)` conjugated by `H`, whose matrix is now its
  `data`. A `frobenius.Functor` maps a spider to the spiders of its codomain
  only when it has no phase: a phased spider is a generator, mapped by
  `ar_map` like any box, where every functor out of `zx` -- `to_map`,
  `to_hypergraph` and `eval` among them -- dropped its colour and its phase;
  a phased `tensor.Spider`, which `Tensor` has no array for, raises
  `NotImplementedError` from `eval` where it evaluated as the phaseless one.
  `gate2zx` decomposes a `Controlled` gate at a distance other than one
  before reading the rotation it controls, where `CRz`, `CRx` and `CU1` at
  `distance=2` gave the two-qubit diagram of `distance=1`, translates
  `Controlled(U1(phase))`, e.g. `CU1(phase).dagger()`, where it raised
  `KeyError`, and its `CRx` and `CU1` evaluate to the gates, where `CRx`
  conjugated both qubits by `H` rather than the target and `CU1` doubled
  its phase and lost a `sqrt(2)`
  ([#625](https://github.com/discopy/discopy/issues/625),
  [#587](https://github.com/discopy/discopy/issues/587)).
- `Diagram.foliation` is an equality up to interchangers, at every level
  of the hierarchy. `Layer.merge` normalised the composite of two layers
  with `normal_form`, i.e. with the rewriting of the diagram's own level,
  snake removal from `rigid` up, so `(g @ snake).foliation()` yanked the
  snake and the README's own `x @ Cap(x.r, x) >> Cup(x, x.r) @ x` crashed
  on the empty diagram it left; `normal_form` takes the rewriting as a
  keyword, `normalize`, and `merge` passes `monoidal.Diagram.normalize`, so
  that it moves boxes by interchangers alone. `to_staircases` split the
  layers with `monoidal.Functor.id`, whose bubble branch rebuilt a `Trace`
  as a `monoidal.Bubble`, so `foliation` and `depth` raised `TypeError` on
  a trace beside another box in any traced or symmetric diagram; it decodes
  the boxes with their offsets instead, which keeps every box as it is where
  the functor of the level would not: `symmetric.Functor` splits a
  permutation into swaps and `frobenius.Functor` drops the phase of a
  spider. `Hypergraph.caps` demanded `left.r == right`, the convention of a
  cup, so every rigid cap of either handedness was refused with an empty
  `AxiomError` and the README's pregroup `Cap(n.r, n) @ Cap(n, n.l) >> n.r
  @ loves @ n.l` could not be foliated, since `foliation` goes through
  `to_hypergraph` first; `cups` and `caps` ask the objects themselves,
  `left.assert_isadjoint(right)` and `right.assert_isadjoint(left)` as
  `rigid.Cup`, `rigid.Cap` and `CMap` do, with a message, the adjoint of a
  type that has none being its reversal
  ([#699](https://github.com/discopy/discopy/issues/699)).
- Coloured regions follow the strands of a crossing.
  `Backend.region_separators` built one separator per edge of a swap, braid
  or permutation, bending at the box node like the wires of any box, where
  `draw_braid` and `draw_permutation` draw each strand as the cubic Bezier
  of `braid_strand`, straight from its input to the output it is permuted
  to: the painted cells pinched into an hourglass at the box centre while
  the wires crossed diagonally, visible as soon as the wires inside a
  permutation carried different colours, since only its outer boundary and
  the adjacent colours within each side are checked. The separators of a
  crossing are now its strands, `region_cells` subdivides the canvas where
  two strands meet — found with `monotone_root`, as the two share their
  height at every parameter — so that no two separators cross inside a
  band, and `region_band` and `draw_region_cell` take a cubic separator
  beside the quadratic ones
  ([#614](https://github.com/discopy/discopy/issues/614)).
- `pip install discopy[grammar]` can import `discopy.grammar.neural`: the
  parser imports `torch` at module level, but `torch` was listed in the
  `quantum` extra only, so an install with the grammar extra alone raised
  `ModuleNotFoundError` on `from discopy.grammar.neural import Parser`.
  `torch` is in the `grammar` extra too, served from the CPU index on Linux
  by the same `tool.uv.sources` entry, and `uv.lock` records it under that
  extra. `import discopy.grammar` still imports no framework, which a test
  pins the way `test/neural/network.py` does for `discopy.neural`
  ([rel-int/discopy-next#52](https://github.com/rel-int/discopy-next/issues/52)).
- `Matrix.then`, `tensor` and `__add__`, and `Tensor.then` and `tensor`,
  built their result as `type(self)(...)`, casting it to the dtype of the
  left operand: the unparametrised structural matrices -- `id`, `swap`,
  the spiders, `cups` and `caps` -- are `int64`, so `Tensor.id(Dim(2)) >> g`
  truncated a float `g` to integers, zeros for one with entries below one,
  as did `Tensor.swap(x, y) >> g @ g` and any spider on the left of a float
  tensor, and a complex tensor on the right of an integer one lost its
  imaginary part, silently. The result is now built in the class
  `Matrix.promote` gives: the one with the dtype the backend promotes the
  two arrays to, read from the operand that already has it, so that
  `Matrix.id(2) >> m == m` for a float `m`, `Tensor[float]`,
  `Tensor[complex]` and `Tensor[Expr]` survive composition with an integer
  structural tensor and `Matrix[bool]` composed with `Matrix[bool]` stays
  Boolean, on the backends whose operations take mixed dtypes at all:
  PyTorch's `matmul` refuses them, as before. The guards of these methods
  check
  `self.ar`, the matrices of the same category whatever their dtype, which
  is what `assert_isinstance(other, type(self))` checked through
  `get_origin` while reading as a check on the dtype. `Tensor.copy`
  defaults `n` to 2 and `Tensor` is an `abc.MarkovCategory` since `Matrix`
  became one ([#538](https://github.com/discopy/discopy/pull/538)); both
  are now tested, the latter by `lens.Markov[Tensor]` building without an
  explicit discard
  ([#733](https://github.com/discopy/discopy/issues/733)).
- `Matrix.swap` wrote the two identity blocks into a zero array in place,
  which JAX refuses: `Matrix.swap(1, 2)` raised `TypeError` under
  `backend("jax")`. It is now `permutation([1, 0], [left, right])`, which
  builds its array from nested lists and so on every backend
  ([rel-int/discopy-next#49](https://github.com/rel-int/discopy-next/issues/49)).
- `biclosed.Application` and `biclosed.Abstraction` are equal when their
  parts are -- function, argument and side; variable, body and side -- as
  the `closed.Compound` terms already were, rather than when they print
  the same between the same types, which is what `cat.Box.setoid`
  compares. A closed constant prints as its bare name, so `c0(c1)` with
  `c0 : a << b, c1 : b` and with `c0 : a << a, c1 : a` compared equal
  while `alpha_eq`, which reads the types of the constants, told them
  apart, and `closed.TermBase.alpha_completeness` failed on the pair once
  the nightly search drew it; a biclosed constant prints with its type, so
  there the two equalities only disagreed on constants differing by their
  `data` alone. Equality and hashing of a term are now structural, i.e.
  recursive, as they were for a `Compound`
  ([#767](https://github.com/discopy/discopy/pull/767),
  [#489](https://github.com/discopy/discopy/pull/489)).
- Three docstrings say what the code does. `discopy.para`'s module
  docstring states that the diagonal `param == copar` is not the state
  monad: the composition of two maps tensors their co/parameters where the
  state category chains one fixed state through, and it points to
  `feedback` and `stream` for iterating a map on its own memory
  ([#683](https://github.com/discopy/discopy/issues/683)).
  `biclosed.Constant` documents its `name: str` and its type rather than
  an `inside` diagram and a `left` flag it never had
  ([#494](https://github.com/discopy/discopy/issues/494)).
  `closed.Diagram.to_term` says that the free variables of its term come
  in the order of their first occurrence in the term rather than that of
  `dom`, so that `eval` gives a diagram with the used inputs in that order
  as domain unless the inputs are passed as its `context`
  ([#693](https://github.com/discopy/discopy/issues/693)).
- `python.Function` is hashable: its dataclass compared `inside`, `dom` and
  `cod` without hashing them, so `jax.jit` refused a function, as did any
  cache keyed on one
  ([#743](https://github.com/discopy/discopy/pull/743)).
- `traced.Trace` loads from its serialisation, which records which side is
  traced: `loads(dumps(f.trace()))` raised `TypeError` from the inherited
  `Bubble.from_tree`, on every level of the hierarchy
  ([#736](https://github.com/discopy/discopy/pull/736)).
- `markov.Copy` and `markov.Merge` load from their serialisation, where
  `loads(dumps(Copy(x)))` raised `TypeError` from the inherited
  `Box.from_tree`, and their daggers go through `merge_factory` and
  `copy_factory`, so that a subclass of `markov.Diagram` daggers its
  copies into its own merges rather than into `markov.Merge`
  ([#736](https://github.com/discopy/discopy/pull/736)).
- A regression test for `stream.Stream.__init__`'s codomain-mismatch
  `AxiomError`, which reports `cod`/`now.cod` rather than the `dom`/`now.dom`
  it once printed on both sides of `!=`. The message was corrected in passing
  by the `+`→`@` object rewrite; the test pins it so a future refactor cannot
  silently reintroduce the bug
  ([#605](https://github.com/discopy/discopy/issues/605)).
- `biclosed.Curry`'s own constructor defaulted to `left=False`, disagreeing
  with `Diagram.curry`'s `left=True` default since #560 unified the two: a
  bare `Curry(box)` curried the opposite side of `box.curry()`, and
  `grammar.categorial.Diagram.bc` passed `n` without `left`, so backward
  composition curried on the wrong side by the same drift.
- A variable of a composite type, e.g. `Variable("v", x @ y)`, is bound
  whole. The abstraction machinery indexed contexts and free variables by
  variable, counting on that index to coincide with a wire index, so such
  a variable used to bind only its last wire in `biclosed`, leaving the
  other one silently free, and crash `Diagram.permutation` in `closed`:
  the context of a term is now mapped wire by wire. This replaces the
  atomicity check on `Variable` that
  [#642](https://github.com/discopy/discopy/pull/642) had added for the
  same bug ([#609](https://github.com/discopy/discopy/issues/609)).
- `closed.Box.is_linear` is a class attribute, so a `Curry`, a `Trace` or a
  `Sum` read as linear whatever they held: `Copy(x) >> f` is not linear but
  its curry, its trace and its formal sum were. Each now reads its inside.
  `monoidal.Sum` pinned `ob = monoidal.Ty`, which came before the diagram
  class in the resolution order of every level's `Sum`, so `closed.Sum.ob`
  and `biclosed.Sum.ob` were `monoidal.Ty` rather than their own types and
  a subclass had to pin its own; the pin is gone, `Sum.ob` is the `ob` of
  the diagram it is a box of, as for every other box.
- `biclosed.Eval`, `Coeval` and `Curry` read back from their `repr` and
  from their tree, and `biclosed.Constant` from its tree: they printed and
  serialised as a `Box`, with a name, a domain and a codomain their
  constructors do not read, so `eval(repr(x))` and `loads(dumps(x))` raised
  `TypeError` on every evaluation, coevaluation and currying, and
  `loads(dumps(c))` on every constant
  ([#398](https://github.com/discopy/discopy/issues/398)).
- `Matrix.trace` reads its `left` flag: a left trace is the right trace
  of the matrix conjugated by swaps, where it traced the last `n`
  dimensions whatever was asked. `Tensor.to_quimb` passes its `dtype` to
  the spiders, as its docstring promised; `Tensor.jacobian` and
  `tensor.Diagram.jacobian` forward their `params` to `grad`, which they
  dropped; `markov.Discard` refuses a number of copies other than zero
  where it swallowed any argument; and `para.Feedback` reads its
  underlying category from `feedback.Diagram` imported as a class, where
  the module name was shadowed by the `feedback` method below it. Every
  one was an unused argument the linter had been reporting
  ([#768](https://github.com/discopy/discopy/pull/768)).
- The marimo notebook previews in the docs follow the theme switch. The
  notebooks are exported with marimo's `system` theme and the docs relay
  the resolved theme into each notebook's iframe through marimo's
  host-theming bridge, since browsers do not forward the page's colour
  scheme into an iframe: only the browser-level preference reached it,
  turning the wires of the adaptive SVGs white on the notebook's white
  background for dark-mode readers. The diagrams drawn inline in a
  notebook read the browser preference rather than the notebook theme,
  so the export inserts a stylesheet keying their adaptive colours to
  marimo's theme class, which outweighs the media query of
  `drawing.backend.DARK_MODE_STYLE`
  ([#453](https://github.com/discopy/discopy/issues/453)).
- `interaction.Diagram.caps` built its inside on `negative @ positive`
  where the constructor asks for `positive @ negative`, so a cap on a type
  with both halves raised `ValueError`; both snake equations hold on such
  a type now. `interaction.Ty.unit` called `natural.unit()`, which an
  `int` or a `tuple` natural does not have: it is `cls()`, the pair of
  empty halves ([#701](https://github.com/discopy/discopy/pull/701)).
- `Hypergraph.rotate` exchanged the two boundaries of the hypergraph and
  replaced each box by its rotation, but left the *ports* of those boxes
  and the spiders where they were: the wires reading a box's domain went
  on reading its domain although the rotated box's domain is its old
  codomain, and a spider typed `a` stayed `a` under a rotation that made
  every port around it `a.r`. Both are invisible on an endomorphism of a
  self-dual type, which is most of what the drawing and conversion tests
  rotate — `test_Hypergraph_rotate` rotated the identity and nothing
  else. Anything else raised: a bare `ValueError` from
  `Hypergraph.__init__` when the two arities differ, an `AxiomError` on
  the spider types when they do not. `.l` and `.r` are involutions again
  ([#716](https://github.com/discopy/discopy/issues/716)).
- `rigid.Diagram.functor_factory` is `rigid.Functor`: it inherited
  `biclosed.Functor`, which does not rotate, so a box mapped through
  it lost the rotation of its boundary.
- Region painting computes the exact extents of each coloured region —
  polygons bounded by the wires on both sides, subdivided per height band —
  instead of overpainting everything to the right of each wire up to the
  full canvas width: translucent colours are no longer painted twice where
  two regions of the same colour are adjacent, white regions are not
  painted at all, so they erase to the background, and neither is the
  inside of a box, which is a 2-cell rather than a region, so no colour
  can bleed out around its border
  ([#521](https://github.com/discopy/discopy/issues/521)).
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
- `kleisli.additive.Channel.trace(0)` no longer empties `dom` and `cod`:
  the tenth `self.dom[:-n]` site of
  [#578](https://github.com/discopy/discopy/issues/578), left to this
  branch since `discopy.kleisli` was not yet on `main` when the other nine
  were fixed by [#588](https://github.com/discopy/discopy/pull/588).
- `no-todo-on-main.yml`'s guard reads the pull request's live `draft`
  field rather than `github.event.pull_request.draft`, a snapshot taken
  when the event fires and stale by however long the event then waited
  for delivery. On [#633](https://github.com/discopy/discopy/pull/633) a
  `synchronize` delivered thirteen minutes late read `false` although the
  guard's own previous run had drafted the pull request fifty seconds
  earlier; the "make ready" branch is gated on that state, so neither
  branch fired and the pull request stayed draft with no `TODO.md` and
  nothing to correct it. The guard also leaves the decision to the newer
  run when the branch has already moved past the event it is handling,
  rather than drafting a head that no longer exists behind its back
  ([#640](https://github.com/discopy/discopy/issues/640)).
- `Matrix` is a `MarkovCategory` rather than a `MonoidalCategory` and gets a
  native `Matrix.permutation`, so a matrix-valued functor applied to a
  diagram with an explicit `Permutation` layer no longer raises
  `AttributeError`. `Matrix.copy` and `Tensor.copy` default to `n=2` like
  every other `copy` in the hierarchy, so single-argument calls such as
  `closed.Application.eval` no longer raise `TypeError`
  ([#535](https://github.com/discopy/discopy/issues/535)).
- `build.yml` timeouts and a bounded, retried Graphviz install
  ([#591](https://github.com/discopy/discopy/issues/591)).
- `python.Function.tensor` is variadic like `monoidal.Diagram.tensor`
  ([#493](https://github.com/discopy/discopy/issues/493),
  [#489](https://github.com/discopy/discopy/pull/489)).
- `closed.Product` parenthesises a first factor of more than one wire at any
  arity but two, as it already did at two: `Product(X @ Y, Z, W)` printed
  `X @ Y.product(Z, W)`, which reads back as `X @ (Y.product(Z, W))`.
- `closed.Product` no longer subclasses the deprecated `biclosed.Ob`
  alias. Its `str` prints `X.product(Y, Z)` rather than `(X * Y * Z)` at
  any arity but two, since the infix form is ambiguous with the pairwise
  nesting `(X * Y) * Z` it is deliberately distinct from and does not
  round-trip through `eval` there. `closed.Functor` routes `Pack`/`Unpack`
  through `pack_factory`/`unpack_factory` instead of always rebuilding a
  `closed.Pack`/`Unpack`, so converting a diagram with either box to a
  `Hypergraph` (or any other non-`Diagram` codomain with product types) no
  longer raises. `Pack`, `Unpack`, `Tuple`, `Projection` and `Let` have their
  own `to_tree`/`from_tree` pair, like `Product` already did, instead of
  inheriting `Box`'s, which builds them with a `name` keyword none of
  their constructors accept
  ([#489](https://github.com/discopy/discopy/pull/489)).
- `frobenius.Diagram.unfuse`'s doctest no longer sets `Spider.color = "red"`
  to draw its example, which was leaking into every later doctest in the
  same pytest process
  ([#522](https://github.com/discopy/discopy/issues/522)).
- Tensor networks are contracted with `opt_einsum` when the number of
  indices exceeds `numpy.einsum`'s 52-index limit
  ([#448](https://github.com/discopy/discopy/pull/448)).
- Contracting a tensor network with more than `config.MAX_EINSUM_INDICES`
  indices imports `opt_einsum`, which is not a declared dependency; a plain
  install now raises a clear `ImportError` naming the package to install
  instead of `ModuleNotFoundError` with no context
  ([#596](https://github.com/discopy/discopy/issues/596)).
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
- A bubble whose inside and outside have a different number of wires keeps
  its boundary. Drawing the sides of a square frame with zero width is now
  the business of `Drawing.slot` and `Drawing.frame`, which have the colours
  of the regions they separate to show the edge in their place, rather than
  of every bubble drawn as a square, which has none and so came out with no
  visible outline at all
  ([#520](https://github.com/discopy/discopy/issues/520),
  [#569](https://github.com/discopy/discopy/issues/569)).
- Controlled gate drawing: the control wire is anchored on the indexed
  input of the controlled box rather than its first one, so gates with a
  classical wire or a distance other than one are drawn on the right wires
  ([#439](https://github.com/discopy/discopy/pull/439)).
- Drawing a discard on more than one wire: `draw_discard` was shadowing the
  layer index with its inner loop counter
  ([#513](https://github.com/discopy/discopy/issues/513)).
- Bugs in `discopy.quantum` reported in
  [#482](https://github.com/discopy/discopy/issues/482): `CQ.__str__`
  printed classical dimensions as quantum, `Measure(override_bits=True)`
  could not be evaluated, `Encode` ignored `constructive`/`reset_bits` in
  its types so daggers were not type-correct, `CRz`/`CRx`/`CU1` raised at
  any `distance` other than one, `Sqrt.dagger` returned `self` so that
  `Sqrt(-1) >> Sqrt(-1).dagger()` evaluated to `-1` instead of `1`, and
  `Channel.cups`/`Channel.discard` hard-coded `Channel` so `Channel[float]`
  silently gave a `Channel[complex]`.
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
- `Channel.tensor` contracts the two arrays directly and interleaves their
  axes, instead of building four boxes, two swap diagrams and a fresh
  `tensor.Functor` on every `@`: ~120x on one tensor and ~12x on
  `eval(mixed=True)` for a four-qubit circuit. `Channel.measure` builds its
  copy spider instead of a Python list comprehension, and
  `Circuit.measure(mixed=False)` reads the Born rule off a single
  contraction instead of running `2**n` of them: ~18x at ten qubits
  ([#482](https://github.com/discopy/discopy/issues/482)).
- `CMap.from_diagram` is linear rather than quadratic in the number of
  boxes: `CMap.from_glued` glues the image of each box onto a scan of
  open wires in a single pass, instead of folding the images with
  `then` and re-validating the whole prefix at every step. This speeds
  up `Diagram.eval` on every tensor backend
  ([#525](https://github.com/discopy/discopy/pull/525)).
- `Hypergraph.from_diagram` is linear rather than quadratic in the number
  of layers, mirroring `CMap.from_glued`: the new `Hypergraph.from_glued`
  glues the image of every box onto a scan of open wires with a single
  union-find pass, instead of folding the images with `then`, which
  recomputes the pushout and relabels every spider and box built so far
  at each layer. A closed loop left by gluing a cap directly onto a cup
  survives as a scalar spider, since it is never referenced by the
  scan and would otherwise vanish silently. This speeds up
  `symmetric.Equation`, `compact.Equation`, `frobenius.Equation`,
  `Hypergraph.simplify` and `Diagram.foliation`, all of which go through
  `Diagram.to_hypergraph`
  ([#623](https://github.com/discopy/discopy/issues/623)).
- `CMap.ports` is a `cached_property`, confirmed with a regression test
  rather than assumed from `CMap`'s immutability: `Hypergraph.from_map`
  reads it once per box, so a plain `@property` rebuilding the whole port
  list on every access made `CMap.to_hypergraph` quadratic in the number
  of boxes, 226 s at 3200 boxes. It is now linear, e.g. 65.6 ms at 800
  boxes and 294.9 ms at 3200, down from 5.4 s and 226 s
  ([#624](https://github.com/discopy/discopy/issues/624)).

### Project

- `fail-under` rises from 8.82 to 8.83, by what `discopy.kleisli.token`
  lifts the score: 9.0105 on `main` and 9.0266 with it, both read with
  `--output-format=json2`
  ([#639](https://github.com/discopy/discopy/pull/639)).
- `fail-under` rises from 8.79 to 8.82, by what `discopy.kleisli` lifts the
  score: 8.85 to 8.88 on the lint job of `main`, 8.969 to 8.998 locally
  ([#443](https://github.com/discopy/discopy/pull/443)).
- `fail-under` rises from 8.77 to 8.79, the score once the terms carry
  their laws ([#767](https://github.com/discopy/discopy/pull/767)).
- `fail-under` rises from 8.75 to 8.77, the score once `closed` gains its
  products and let statements
  ([#489](https://github.com/discopy/discopy/pull/489)).
- `CONTRIBUTING.md` tells a sandboxed contributor to diff its test-suite
  failure set against the same run on the merge base, so that a failure
  already present there reads as pre-existing rather than as a regression
  the change introduced, and to claim local green only for the checks run
  locally, with CI on the pushed branch the authority on the real suite
  ([#499](https://github.com/discopy/discopy/issues/499)).
- pylint reads a law stated with `@axiom` as the classmethod it is,
  through `.github/scripts/pylint_axioms.py`, a plugin `.pylintrc` loads
  and `.github/tests` checks: the decorator returns a descriptor binding
  the law to its category, and astroid infers a classmethod from the
  `classmethod` decorator alone, so every law read as a method wanting
  `self`, with the members of its category read as those of an instance.
  The configuration also declares the `factory` a `NamedGeneric` subscript
  sets and the `*_factory` attributes a module sets after its class as
  `generated-members`, lets `hypothesis.strategies` be imported where a
  strategy is built, the convention keeping hypothesis out of the
  package's imports, and reads the code as the 3.12 that `pyproject.toml`
  requires rather than 3.10. `cyclic-import` is disabled: the package
  imports every module, so the graph is cyclic by design, and pylint
  reported 63 cycles on one run of `main` and 67 on the next, moving the
  score by a hundredth between two runs of the same tree, which a
  threshold cannot tolerate. `fail-under` rises from 8.58 to 8.75, the
  score of `main` once these categories are gone, the first four of the
  ones [#770](https://github.com/discopy/discopy/issues/770) lists
  ([#776](https://github.com/discopy/discopy/pull/776)).
- The `lint` job fails on any unused import, variable, argument, wildcard
  import or private member, and on a pylint score below `fail-under`, set
  to the score of `main` at the time so that it never goes down:
  `.pylintrc`'s `fail-on` names the six messages, `fail-under` rises from
  7 to 8.58, and its `suggestion-mode` option, which the pylint in the
  lock no longer knows and reported as an error on every run, is gone.
  The 65 findings on `main` are fixed or excepted explicitly on their
  line with the reason: the re-exports carry `pylint: disable` beside
  their `noqa`, and the drawing backend's interface primitives keep the
  parameters a backend reads. `AGENTS.md` and `CONTRIBUTING.md` list
  `pylint discopy` beside `pflake8`, and `CONTRIBUTING.md` says what to do
  with a finding and when to raise the threshold. Proposed on
  [#767](https://github.com/discopy/discopy/pull/767#discussion_r4040064818)
  after an unused parameter was the whole bug
  ([#768](https://github.com/discopy/discopy/pull/768)).
- The docs build on Sphinx 7.4 rather than 7.2, whose `stringify_annotation`
  handled a `TypeVar` but not a `ParamSpec`, so a signature such as
  `Callable[Concatenate[type, P], T]` crashed autodoc on Python 3.14, where
  `typing.get_type_hints` resolves the PEP 695 type parameter. The pin and
  the lock move, `myst-parser == 2.0.*` allowing any Sphinx below 8, and the
  `drawing`, `grammar`, `python` and `quantum` API pages list their
  submodules without the module prefix, which Sphinx 7.4 warns against
  under `automodule`
  ([#722](https://github.com/discopy/discopy/issues/722)).
- `CONTRIBUTING.md`'s LLM guidelines require an LLM contribution to be
  authored under a GitHub handle separate from the human who prompted it,
  and a pull request authored by an LLM to be approved by at least one
  human other than the one who prompted it.
- `.claude/hooks/session-start.sh`, registered in `.claude/settings.json`
  as a `SessionStart` hook for Claude Code on the web, syncs the full
  development environment before the session starts, so that the linter
  and the whole test suite run as `CONTRIBUTING.md` says; without the
  registration the script is inert. When `download.pytorch.org`, the index
  `pyproject.toml` pins torch to on Linux, is not reachable from the
  session, it syncs everything but torch and installs the locked version
  from PyPI instead, whose wheels run on the CPU. Every agent session so
  far ran `pytest --skip-extra` and reported the torch tests skipped.
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
