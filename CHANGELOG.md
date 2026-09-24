# Changelog

All notable changes to DisCoPy are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Changes since [`1.2.2`](https://github.com/discopy/discopy/releases/tag/1.2.2).

### Added

- `discopy.pattern` and `discopy.search`, the language in which a
  category states its structure and the proof search generating its
  terms, serving two ends: the equations of the axioms of
  `discopy.axioms`, canonical or generated, and diagrams built from
  rules toward a goal pattern.
  A category states its structure as the typed signatures of its
  methods, which `parse` collects into sequents. Every annotation is
  an `Annotated[T, pat]`, the coarse type a typechecker reads beside
  the one pattern the interpreter builds, and the metavariables are
  the declaration's own PEP 695 type parameters, nothing imported: a
  rule reads `def then[A, B, C](self: Annotated[C1, Hom[A, B]],
  other: Annotated[C1, Hom[B, C]]) -> Annotated[C1, Hom[A, C]]` — the
  base `C1` is what a typechecker sees, so the laws typecheck on the
  cells they compose — a kind is the bound, `def cups[X: Atom]`, the
  boundaries of a higher cell are declared on its binder, `def
  tensor[X, Y, A: Annotated[C1, Hom[X, Y]], ...]` mimicking the
  telescope `{A : C1 X Y}` of a dependently typed language, and a
  compound pattern is a pattern class subscripted with the type
  parameters — `Hom[Tensor[X, R[X]], Unit[C0]]` for the cups — whose
  subscript *is* the pattern: the interpreter builds it when the
  declaration is defined, a `Hom` taking its level from the base of
  the `Annotated` carrying it. The subscript is the one spelling of
  the language. Each pattern class declares its level, the least
  structure the objects it stands in must have — `Unit` and `Tensor`
  a `ColouredMonoid`, `Adjoint` (`L[X]`, `R[X]`) a `Pregroup`,
  `Delay` the new `abc.DelayedMonoid` that `feedback.Ty` is, `Exp`
  (`Over[X, Y]`, `Under[X, Y]`) a `ResiduatedMonoid`, `Repeat[X, N]`
  the legs of a spider — and is typed in one of two ways: `Var`,
  `Adjoint`, `Exp` and `Sequent`, which no annotation subscripts, are
  generic in the colours `C0` and objects `C1` with the level as the
  bound of `C1`, while the classes standing in annotations are
  generic in what their subscript takes, since a typechecker reads
  that subscript as a specialisation and would arity- and bound-check
  the metavariables against a `C0, C1` parameterisation, and declare
  their level as a classmethod.
  `C0` and `C1` name both the type parameters of the class stating
  the law and the `Sort`s the annotations of a module-level
  declaration name; a premise may also be a bare sort — `f: C1`,
  `term: Self` — quantifying over the arrows or terms themselves.
  Nothing is `eval`ed and nothing is quoted: the annotations are the
  lazy objects of PEP 649, evaluated by the interpreter in their
  defining scope when read — a forward reference such as the
  `Diagram` of `symmetric.Diagram.cycle` staying a plain name until
  the class exists — and `parse` collects each sequent shallowly from
  `__annotations__`, `__type_params__`, `__bound__` and
  `__metadata__`, objects built in the scope PEP 695 gives them, so
  unification across a declaration holds by construction and the
  environment that impersonated `Annotated` around an `eval` is gone.
  A conclusion is matched against a goal by unification over the free
  monoid of objects — a `Tensor` splits the goal at every position, a
  `Var` binds once, an adjoint inverts to the other side — and what
  matching cannot invert is a residual equation checked once the
  variables are instantiated.
  `monoidal.Diagram.strategy` is the one goal-directed search by the
  `rules` and `generators` a category declares, every level inheriting
  it as is: the sides of a trace, an evaluation, a currying and a
  feedback are their own typed rules (`trace_left` and `trace_right`,
  `ev_left` and `ev_right`, `curry_left` and `curry_right`,
  `feedback_left` and `feedback_right`, with `trace`, `ev`, `curry`
  and `feedback` helpers taking `left`, and a `Feedback` takes its
  memory on the left too), `braid_inverse` and `symmetric.Diagram.cycle`
  — a native permutation of any length — join the generators, a
  fixed vocabulary is a dictionary of `Rule.constant` boxes (the words
  of a pregroup grammar, the gates of a circuit) whose search leaves
  out the free box, a dead-ended goal is retried a bounded number of
  times before the example is rejected, and a term built
  outside its declared conclusion is an `AxiomError`.
  `pregroup.Diagram.strategy` draws a sequence of words reduced onto
  the goal by `eager_parse`, rejecting an utterance the parser
  rejects, where the generic walk almost never meets a grammatical
  one. `cat.Arrow`
  keeps a recursive path strategy and `cat.Functor` enrols in the
  matrix with `Relabelling` endofunctors and its own classifications —
  for the functors whose domain has objects freely generated by names,
  the others staying unchecked. A functor class brings four sorts on
  top of `C0` and `C1` (which for a functor category are the
  categories and the functors): `In0`, `In1`, `Out0` and `Out1`, the
  objects and arrows of the categories it maps from and to, read off
  its `dom` and `cod` — the sorts of the two overloads declared on
  `Functor.__call__`, `In0 -> Out0` on objects and `In1 -> Out1` on
  arrows. Functor laws quantify their functor with `Self` and their
  source with these, e.g. the `Equivalence` laws draw `f: In1`, and a
  level's functor declares the axiom for its own structure in its
  class body — `braided.Functor.braided`, and
  `symmetric.Functor.symmetric` preserving the swap on `Atom[In0]` —
  rather than functors inheriting a generic one: in practice each
  level adds one more axiom sending the extra structure of its `dom`
  to the same generator of its `cod`. The dagger laws
  of biclosed and closed diagrams are inapplicable, a curried diagram
  having no dagger, and `proptest/conftest.py` suppresses
  `filter_too_much` again, the search rejecting by design: a dead-ended
  goal rejects its example and a law weakened to a subspace filters
  what the search draws. The `TwoCategory` levels, the goals-with-holes
  search, the `Choice` patterns and the argument-shape wrappers of the
  earlier experiments are retired.
- The conversion, rewriting and drawing laws of the free diagram
  categories, stated as axioms on the classes introducing the methods
  and checked by the matrix, absorbing `proptest/test_conversion.py`,
  `test_normal_form.py` and `test_drawing.py` (with `categories.py`,
  their parameter list) the way the serialisation axioms absorbed the
  ad-hoc property files. `monoidal.Diagram` states `hypergraph_section`
  (`to_diagram` is a section of `to_hypergraph`),
  `map_hypergraph_agreement` (encoding through a map or directly gives
  the same hypergraph), `staircase_encoding` (`decode` undoes `encode`
  up to the level's own equation), `normal_form_idempotence` and
  `normal_form_soundness` (a normal form is a canonical representative,
  equal to its diagram in the symmetric quotient, on the
  boundary-connected subspace where it is defined),
  `foliation_idempotence` and `foliation_soundness`, `drawing_identity`
  (`to_drawing` preserves identities on the nose — not composition or
  whiskering, the layout spacing wires from the widths of everything
  the diagram contains) and `matplotlib_determinism` with
  `tikz_determinism` (rendering twice gives the same bytes, which also
  renders every generated diagram on both backends, where the old suite
  smoke-tested them). `map_section` and `map_retract` are stated on
  `symmetric.Diagram`: a map is compact whatever category hosts it, so
  decoding one asks for swaps and the laws live where the swaps are —
  the old suite's `monoidal` cell passed on the luck of its draws, a
  map recording no offsets for its states where a hypergraph does, and
  the failure survives weakening to the boundary-connected subspace.
  The section holds modulo the hypergraph, which does not order the
  boxes: a diagram orders its boxes totally where a map orders them
  only by their wiring, so decoding picks one topological order among
  the diagrams of the same map and re-encoding can permute independent
  boxes — the old suite's on-the-nose assertion was falsifiable, its
  draws never having met two independent boxes decoded in the other
  order. The retract is new: decoding the map of a diagram gives back an equal
  diagram in the quotient of the level's own `Equation`, which with the
  section makes the free category, up to its equation, equivalent to
  its image in `CMap`. The quotient is essential — a map is spacial,
  unable to distinguish nested scalars from scalars side by side, and
  so is the hypergraph the equation compares by, while the syntactic
  comparison up to `foliation` is falsified even on the
  boundary-connected subspace, where the doctest example of
  `to_hypergraph` might suggest it holds. `Axiom.weaken(boundary_connected=True)`
  quantifies a law over the subspace `normal_form` is defined on,
  through the one subspace parameter of `Diagram.strategy`; a new
  subspace earns a new explicit parameter when a law needs it. The
  full matrix, collectable again, showed two latent failures of the
  weakened laws: the equations of a weakened law now stay in the
  subspace — a state and an effect are each boundary-connected while
  composing into a closed component, on which the `bifunctoriality`
  of two boxes was compared by a normal form that is not defined
  there — and `closed.Diagram` re-declares `dagger_monoidality`
  inapplicable, `markov` having re-enabled through the diamond what
  `biclosed` declares a curried diagram cannot have. The permutation test
  is subsumed: the strategy draws native permutations through the
  `cycle` generator, so the section and staircase laws exercise their
  encoding, and `abc` states `swap_inverse`. The level lists and xfail
  marks of the old suites become classifications on the level each
  concerns, verified against observed failures rather than transcribed:
  decoding a braid, trace, cup or cap crosses wires that need swaps, so
  `hypergraph_section` is `.failing` on `braided`, `traced` and
  `pivotal` (reaching `balanced` and `ribbon` through them) and
  re-declared on `symmetric`; `to_hypergraph` rejects a left-handed cup
  or cap, so `rigid` declares `hypergraph_section`,
  `map_hypergraph_agreement`, `normal_form_soundness` and both
  foliation laws `.failing`, each re-enabled on `pivotal` with the
  agreement and foliation laws weakened to the boundary-connected
  subspace its `to_hypergraph` asks for; the two encodings differ by
  design from `markov` on, a copy being a spider in a hypergraph and a
  box in a map, so the agreement is `.inapplicable` there. Two of the
  old marks did not reproduce at a 300-example budget and are gone:
  `biclosed` and `compact` hold `hypergraph_section`, and `feedback`
  holds `map_section`. `balanced.DualRail` declares
  `strategy = no_strategy` — one functor rather than a category of
  functors, whose inherited relabelling strategy crashed the collection
  of the full matrix on `cat.Functor.identity_typing` — and
  `Hypergraph.cups` and `caps` raise their `AxiomError` with a message
  where they raised it bare.
- `cat.Equivalence` and `cat.Inverse`, a functor with an inverse: the
  functor is `__call__`, the inverse is `decode` and `dagger` wraps it
  as the `Inverse` functor from the codomain back — the first functors
  whose domain is a concrete category rather than a free one. Functors
  given by mappings compare unequal to the identity functor (#648), so
  the laws of `F >> F.dagger() == Id() == F.dagger() >> F` are
  quantified pointwise: `retract` over the arrows of the domain, up to
  the equation of the domain category, and `section` over their images,
  beside the `composition` and `identity` any functor preserves, stated
  here for the first time — the image of an arrow is the composition of
  the images of its two halves, which is the correctness of the glued
  encodings. The laws of the functor category — associativity, typing,
  unitality — are inapplicable, one functor not being a category of
  functors, and an equivalence pickles as its class alone, its codomain
  being a parameterised class that does not pickle by reference.
  `monoidal.Diagram.ToHypergraph` and `symmetric.Diagram.ToMap` wrap
  the conversion methods as generators, so every level gets its own
  equivalence by the same diamond as its diagrams and the
  classifications inherit with it: the cells of the conversion laws
  move from the diagram classes onto the equivalences —
  `hypergraph_section` becomes `ToHypergraph.section`, failing on
  `braided`, `traced`, `rigid` and `pivotal` and re-enabled on
  `symmetric`, `map_section` and `map_retract` become the laws of
  `ToMap`, the section still modulo the hypergraph — while the
  agreement, staircase, rewriting and drawing laws stay where they
  were. `ToHypergraph.retract` is declared failing on `monoidal`,
  whose syntactic equation decoding cannot land back on, re-enabled
  from `symmetric` on where the equation is the hypergraph quotient;
  `rigid.ToHypergraph.composition` fails on the left-handed cups its
  encoding rejects and comes back on `pivotal`, which encodes both
  orientations. The new laws found one violation the old suite's draws
  never met: decoding the map of a closed diagram re-whiskers the
  inside of a curry bubble, which the hypergraph of a bubble compares
  syntactically, so `closed.ToMap.retract` is declared failing. An
  equivalence whose domain does not generate stays unenrolled, e.g.
  over `tensor.Diagram`, and `Inverse` declares
  `strategy = no_strategy` like `balanced.DualRail`.
- The whole unified tree typechecks: `uv run --with ty ty check` passes
  in the full development environment (`uv sync --dev --group all`, the
  reference for typechecking now that the optional imports carry no
  ignore comments), with the same two rules off as before, documented
  in `pyproject.toml`. The `Generator` descriptor declares `Any` on
  attribute access, since a typechecker takes only a class object or
  `Any` for the base classes a module builds on it, and the
  `FreeCategory.generator` decorator keeps the class it declares,
  `type[U]` to `type[U]`, so every generated factory stays a class to
  the typechecker.

- The codebase typechecks: `uv run --with ty ty check` passes, configured
  by the `[tool.ty]` sections of `pyproject.toml`. A first annotation pass
  declares the factory class attributes assigned after each class
  definition, the box drawing attributes that :mod:`discopy.drawing` sets
  on :class:`monoidal.Box`, and makes every parameter defaulting to
  ``None`` optional. The lazy imports of optional dependencies and the
  remaining dynamic constructions are ignored inline. Two rules stay
  off, documented in `pyproject.toml`: `invalid-method-override`, since
  aligning the n-ary signatures that the tower narrows means changing
  runtime APIs, and `unresolved-attribute`, since the downgrade paths of
  `Hypergraph` and `CMap` ask the host category for structure behind
  runtime guards, `Node` holds arbitrary data and implementations are
  borrowed across levels.
- `NamedGeneric` is reimplemented on PEP 695 type parameters: the
  parameter is declared with the class syntax, e.g.
  ``class Diagram[dtype]``, instead of a string subscript, so
  typecheckers understand a specialisation like ``tensor.Box[complex]``
  both as a value and as a base class. The runtime machinery is
  unchanged: subscripting with a concrete value builds a cached subclass
  carrying it as a class attribute, named and pickled as before, while
  subscripting with the class syntax's own parameters, as in
  ``class Box[dtype](Diagram[dtype])``, delegates to `Generic`, and
  subscripting with an explicit `TypeVar` builds a carrying subclass
  like any other value. `NamedGeneric` lives in `discopy.utils` and
  `List` and `axioms.Equation` declare their parameter with the class
  syntax too.
  `CMap` and `Stream` are parameterised by a category bounded by the
  diagrams they host, para maps by a symmetric one, and `Stream` defines
  its own `later`, `head`, `tail` and `is_constant` properties instead
  of borrowing the descriptors of `Ty`.
- The abstract base classes bound their type variables all the way down
  the tower and declare the structure their methods assume: a length and
  slices on the objects of a `ColouredMonoid` and the exponential
  accessors on a `ResiduatedMonoid`. `Self` return types express the
  covariance the tower used to assert: `Box.dagger`, the adjoints of
  rigid types, the integer power of a monoidal type, braids built by the
  hexagon equations, tensor compositions and the lifts of parametric
  maps all land in the class of their caller.
- The style review can be asked for, and turned off, from the pull request
  itself: `@discopy review this` in a comment reviews it now, and the
  `no-style-review` label stops the automatic reviews on it, while the
  comment goes on working — it is "stop reviewing this on its own", not
  "never review this". The comment is read from people with write access
  only, and labelling already is, so nobody who can merely comment can
  silence the reviewer or spend the gateway budget. It replaces the
  `style-review` label, which did the same on demand except that it never
  handed over to the correctness reviewer. A pull request already open and
  not about to change had no trigger at all otherwise, since only a push
  reaches one ([#638](https://github.com/discopy/discopy/issues/638)).
- A `fast` Hypothesis profile in `proptest/conftest.py`, the settings of
  `dev` under which the matrix keeps one cell per declaration of a law:
  the enrolled type nearest the class declaring it, so that a law is
  tested once bound to its defining class rather than again on every
  type inheriting it, a type restating an inherited law — broken,
  weakened or modulo a quotient — declaring it anew. It is the profile
  to develop with, 82 cells where the full matrix has 936, see
  `CONTRIBUTING.md`. The laws declared broken are checked apart, by
  `test_broken_axiom`, without the phases that shrink and explain the
  counterexample: the first one is enough to confirm the declaration, and
  `Axiom.falsify` shrinks one on demand, where the shrink of a single
  `#742` roundtrip took a hundred seconds of every run.
- `abc.Category.generators`, the logical constants the search builds in
  one step — the structural boxes of the level and the identity —
  adjusted by assigning a dictionary of rules on a class,
  `Rule.constant(box)` giving the rule of one given box.
  `pregroup.Diagram` is generated by the words of `pregroup.VOCABULARY`,
  *Alice loves Bob*, and the cups reducing them, so that
  `pregroup.Diagram.strategy()` draws grammatical sentences, from the
  empty type to the sentence type by default, and
  `quantum.circuit.Circuit` by the gates of `quantum.gates.GATES` that
  take no parameter and the swap, so that `Circuit.strategy(dom=qubit **
  2)` draws circuits on two qubits; a grammar or a gate set assigns its
  own generators on a subclass. Neither traces, both dropping the trace
  rules on either side, and neither is a cell of the matrix: a category
  whose generators are the `Constant` rules of a vocabulary fills only
  the sequents that vocabulary derives, not the ones a law draws, and
  `proptest/test_axioms.py` keeps to the free categories.
- `Axiom.canonical`, the law as a schema: its equation on the canonical
  arguments of its pattern, each metavariable an object named after it
  and each arrow a box named after its parameter — `Equation(f >> g >>
  h, f >> g >> h)` for associativity — and `Axiom.draw`, drawing it;
  `Declaration.canonical` gives the canonical arguments of any sequent.
- `Axiom` is a `Testable` whose terms are its equations: `Axiom.pattern`
  is the `Signature` of its annotations, whose strategy is the input of
  the law, and `Axiom.strategy` returns a `SearchStrategy[Equation[T]]`,
  the law mapped over it, filtered by the subspace of a weakened law;
  `Axiom.falsify` returns the false equation rather than the arguments,
  the one a law declared broken raises included, and finds none when a
  law declared broken holds on every example. The matrix and
  `assert_axioms` draw equations and assert them.
- `feedback.Discard` and `closed.Merge`, the discard of a feedback
  diagram and the merge of a closed one: `feedback.Diagram.copy(x, 0)`
  built a `markov.Discard` and `closed.Diagram.copy(x).dagger()` a
  `markov.Merge`, neither a diagram of its own category, which the copying
  rule met at once; `markov.Copy.dagger` and `markov.Merge.dagger` now go
  through the level's `merge_factory` and `copy_factory`.
- A dagger braid reads back from its tree: `is_dagger` is one of
  `braided.Braid`'s `serialised_attrs`, where the tree of `Braid(x, y,
  is_dagger=True)` used to decode as the braid over, met by the search
  once its braiding hint read the sequent.
- `monoidal.Colour.from_tree` reads back the transparent colour, whose
  `name` its tree omits as the default. The laws every enrolled level now
  faces are classified where they break: `monoidal.Wire.repr_transparency`
  is declared failing ([#650](https://github.com/discopy/discopy/issues/650)),
  the dagger laws are inapplicable to rigid types and diagrams and back
  for pivotal ones, and the roundtrips of a trace, an evaluation, a copy,
  a twist, a spider and a feedback box, which the generic `Serialisable`
  machinery does not fit yet, are declared failing on the level introducing
  each box under the umbrella
  ([#742](https://github.com/discopy/discopy/issues/742)), re-enabled where
  the hierarchy's diamonds would otherwise skip a level that passes.
- `axioms.Serialisable`, the serialisation interface of DisCoPy, one hook
  driving all three mechanisms: the class attribute `serialised_attrs`
  names the attributes that are also keyword arguments of `__init__`,
  from which follow a generic pair of inverse methods `to_tree` and
  `from_tree`, a generic `__repr__` such that `eval(repr(x)) == x`, and
  `__setstate__` for the pickle protocol. A class with a different
  constructor declares its attributes
  once instead of reimplementing each method: `cat.Ob`, `Arrow`, `Box`,
  `Sum` and `utils.BinaryBoxConstructor` drop their hand-written
  `to_tree` and `from_tree` pairs for declarations that produce
  byte-identical trees, and `cat.Ob`, `cat.Box` (all but its dagger
  case), `rigid.Box` and `BinaryBoxConstructor` drop the hand-written
  reprs the generic one reproduces. An umbrella issue collects every
  implementor still missing
  ([#742](https://github.com/discopy/discopy/issues/742)). An arrow
  decoded by the generic method has its composition checked again, where
  `Arrow.from_tree` used to skip the check, and an explicit
  `"is_dagger": false` in a tree decodes as `False`, where the old
  key-presence test read it as `True`.
- Each mechanism comes with the law that it is a roundtrip, stated on
  `axioms.Serialisable` as an axiom like any other: `repr_transparency`
  for the
  representation, `pickling` and `copying` for the pickle protocol and
  `serialisation` for the tree, with `environment` for the namespace a
  representation reads back in. `copying` is new — a deep
  copy goes through the same reduction as a pickle without the bytes,
  which is how the `NamedGeneric` parameters were lost below. Stating an
  axiom is no longer the business of `Category` alone: both it and
  `Serialisable` subclass `axioms.Testable`, which carries the `axioms`
  classproperty they share, so that a type stating the roundtrips
  without being a category — the objects of a category, say — is
  enrolled like the rest. One class both states the laws and says how to
  draw the terms they quantify over, since the two never come apart in
  practice: every abstract base class that states laws is one a subclass
  will generate eventually, and the wrappers that generate a law's
  arguments — `Grid`, `ComposablePair`, `ComposableTriple` — state the
  composability their constructor enforces, rather than being generators
  of nothing.
  `Testable.strategy` is deliberately not an `abstractmethod`: that would
  make every category which has not implemented one uninstantiable
  rather than merely unchecked, 66 concrete classes among them, so the
  default raises `NotImplementedError` instead. `Testable.subclasses`
  walks the transitive subclasses and `proptest/test_axioms.py` reads
  the matrix off it, rather than off a list kept beside the suite: a
  class enrols itself by implementing `strategy`, and one that would
  inherit a strategy for the wrong terms — a `monoidal.Ty` is not the
  `cat.Ob` it subclasses — declares `strategy = no_strategy` until it
  implements its own. So a category states its laws from the moment it
  has them, is checked as soon as it says how to generate their terms,
  and says which of the two it is where it is defined. That is `cat.Ob`,
  `cat.Arrow` and `cat.Box` to begin with, where the matrix reached the
  objects and boxes only through the arrows containing them; the eight
  classes below them that generate nothing yet — `cat.Sum`,
  `cat.Bubble` and the six of `monoidal` — carry the opt-out.
- `utils.Generator` declares a generator once, on the category that
  introduces it and under its own name: `@Diagram.generator` above
  `class Swap` in `symmetric` binds `Diagram.Swap`, with a `ClassVar`
  annotation for it in the body of `Diagram`. Naming the attribute after
  the class couples the two, so a category reads `cls.Swap` where it used
  to read `cls.swap_factory` and `cat.FreeCategory.generator` needs no
  name of its own. That name was taken: the `generator` of an `Arrow`,
  `Ty`, `Layer`, `Diagram`, `Sum` or `Hypergraph` -- the single box or
  object of a term that has exactly one -- is now its `atom`, with
  `is_generator` following as `is_atom`, which is what a term of length
  one is. `Sum.atom` is a property like the other five, where it was a
  method returning itself. Every level below
  gets its own subclass built on first access, extending the swaps of its
  bases, the generators its root extends (a swap is a permutation, a
  discard a copy) and the level itself, so a module writes
  `Swap = Diagram.Swap` in place of `class Swap(markov.Swap, Box)`
  and `Diagram.swap_factory = Swap`; a level adding behaviour declares it
  again, a generator that is behaviour rather than a class is a
  `Generator.classmethod`, e.g. the trace of a pivotal diagram, one that is
  another generator of the same category a `Generator.alias`, e.g. the braid
  of a symmetric category is its swap, and a class attribute assigned by
  hand still wins. Two slots name a role rather than a class, since they
  are read on whichever free monoid or category is at hand: a stream
  answers to `FollowedBy`, and a `List` names the class of its atoms
  `Atom` where a `Ty` names its generators `Wire`, since `Atom` types
  what a list is made of and `ob` what it goes between. `abc.Category.equation_factory` becomes `Category.Equation`
  and each level binds the `Equation` it declares, where every one of them
  read `cat.Equation`: an axiom of a category that quotients its equations
  is now checked up to that quotient, e.g. by hypergraph isomorphism from
  `symmetric` on, as the slot always said it would be.
  `Generator[**P, T]` is generic in
  the parameters of its generator and the instance it builds, `subclass`
  and `classmethod` scoping their own, so that a binding carries the
  signature of its root and a `ClassVar` spelling that signature out is
  checked against it; `__get__` returns `Callable[P, T]` and `__call__`
  takes `P` to `T`, for a generator read off the class that declares it. Fifty-six
  trivial subclasses go, and every generator a level builds (bubbles,
  sums, traces, copies, merges, evaluations) is a diagram of that level
  rather than of the level that introduced it. Roots initialise through
  `self.Box.__init__`, i.e. the box of the level they are
  built in, so the six `z = 0` of the ribbon generators go where a braid
  used to have no winding number of its own, `feedback.Swap`, `Copy` and
  `Merge` keep only their `delay`, and `ribbon.Functor` recognises any
  `balanced.Braid`. `cat.Arrow`
  type-checks its boxes itself, `pivotal.Box` is a `traced.Box` and
  `closed.Diagram.is_linear` reads its boxes. The same declaration serves
  types, terms and functors: a `Ty` declares its wire, `biclosed.Ty` its
  exponentials, `biclosed.Diagram` its terms with
  `Ty.Constant = Diagram.Constant` linking the two at each
  level, and every `Diagram` its `Functor`. A built class is tied to its
  level by its root: it extends the level when the root is a subclass of
  the owner, and the class attributes of the root equal to the owner are
  lifted, so a built `Exp` has the level's `Ty` as `ob` and a built
  `Functor` the level's `Diagram` as `dom` and `cod`. A generator is built
  once per module, `Nat` and `Dim` sharing those of their `Ty`.
  `categorial.Over` and `Under`, `pivotal.Functor` and `pregroup.Functor`
  go, `biclosed.Ty` is made of the `biclosed.Wire` it never used, and the
  braided, ribbon, pregroup and circuit diagrams have their own
  `Functor` where they inherited a higher level's. `Layer`
  is a `Generator` like the rest, so every level has its own `Layer` rather
  than the one of the level that last added behaviour to it: a diagram
  names its own layers when it serialises, and a layer built by hand from
  a parent's class is not equal to one of the level below, as was already
  the case for boxes. A factory class whose `ar` has no generator in its
  bases, e.g. `grammar.cfg.Tree`, keeps the root of the declaration rather
  than raising `ValueError`.
- `abc.DaggerCategory`, a `Category` with an abstract `dagger`, so that the
  dagger laws — contravariance and involution — are stated only where there
  is a dagger. `cat.Arrow` inherits it, and the diagram classes inherit it
  down the hierarchy, while `cat.Functor` and `monoidal.Ty` do not: a functor
  has no dagger and a type's generators need not either, so the property
  tests of [#658](https://github.com/discopy/discopy/pull/658) can generate
  the dagger axioms for the carriers that declare one instead of every
  carrier opting out by hand. `cat.FreeCategory` keeps the implementation —
  reversal by slicing, shared with `monoidal.Ty` — without the
  declaration. `matrix.Matrix`, `hypergraph.Hypergraph` and `cmap.CMap`
  declare it too: the conjugate transpose and the boundary swaps are
  daggers of their own
  ([#731](https://github.com/discopy/discopy/issues/731)). Merged into
  this branch, the entry above holds with two adjustments: the laws
  keep their `Annotated` spelling, and the inapplicable declarations
  they replace go where the laws are gone — `cat.Functor`'s and the
  rigid and biclosed types' — while the levels that re-enable or
  restate them, `pivotal` and `biclosed`, read them off
  `DaggerCategory`. `cat.Equivalence` becomes the
  `Equivalence(Functor, DaggerCategory)` first asked for: its
  involution holds on the nose, restated over the one functor, and its
  contravariance is inapplicable like the rest of the functor-category
  laws.
- `monoidal.List`, the free monoid on a generator type: `List[X]` is a
  tuple of instances of `X` with concatenation as `tensor` and the empty
  list as unit, an `abc.Monoid` parameterised as
  `NamedGeneric["Atom"]` the way `Hypergraph[C]` is the
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
  demand. `Testable.strategy`
  generates the terms a law quantifies over, whatever its level, while
  the laws that a term reads back from its representation, its pickle
  and its tree are stated on `axioms.Serialisable` above; the ad-hoc property
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

- `cat.Functor.strategy` relabels endofunctors only: a relabelling
  sends the domain's own generators to each other, so the functors into
  another category — tensors, intertwiners, channels — stay unchecked,
  as their docstring promised, instead of failing the functor laws on
  relabellings their codomain cannot type, and `grammar.cfg.Algebra`,
  whose domain is an operad of trees rather than a free category,
  declares `strategy = no_strategy`.
- The laws a curry bubble breaks are classified where they break:
  mapping a bubble decodes the map of its inside, which re-whiskers its
  states, reorders its independent boxes and can ask a planar category
  for swaps, while the hypergraph of a bubble compares its inside
  syntactically — so `biclosed.Diagram` declares
  `map_hypergraph_agreement` failing, and `closed.Diagram` declares
  `staircase_encoding` failing, whose roundtrip decomposes the
  permutations inside a bubble into swaps, both found by the matrix.
  `biclosed.Diagram`'s currying laws carry the reason of their
  recorded counterexample — a free currying is a bubble, equal to its
  evaluation only semantically — where they cited the fixed #562.
- `Rule.apply` applies the keyword-only parameters of a rule's method
  by the names of its premises, so `feedback(*, left)` and friends
  apply, and the rest positionally in premise order, which variadic
  methods such as `Arrow.then` need. `Rule.constant` is declared in the
  body of `Rule` and `pattern.interpret` refuses a type variable that
  is neither a parameter of the declaration nor a sort in scope, where
  it crashed with `KeyError` on the stray name. `parse` level-checks
  the bounds of binders, `Tensor` refuses a subscript of fewer than two
  operands, where `Tensor[()]` crashed with `IndexError`, `Repeat`
  refuses a non-atomic base, which matching cannot read back, the
  `__str__` of an adjoint or delay parenthesises a compound base, so
  `R[Tensor[A, B]]` prints `(A @ B).r` rather than `A @ B.r`, and the
  pattern docstrings stop promising an `@` operator on patterns.
- Broken marks stop at the level where the law holds again:
  `braid_naturality` is re-enabled on `symmetric.Diagram` — a free
  braid is a box, but the braid of a symmetric category is its swap,
  whose naturality holds in the hypergraph quotient — and
  `markov.Diagram` declares its `repr_transparency` and
  `serialisation` under the copy's own reason, its `__new__` wanting
  its type (#742), where they were recorded under the trace's.
- `cat.Equivalence.dagger_involution` is declared inapplicable — the
  dagger of the inverse is the equivalence itself by construction, so
  there is nothing to check — and both `Equivalence` and `Inverse`
  hash consistently with their equality, an equivalence by its class
  and an inverse by the equivalence it inverts.
- `monoidal.Diagram.to_drawing` names its optional parameter `functor`
  rather than `functor_factory`, after the slot rename that removed
  the `*_factory` convention.
- DisCoPy requires Python 3.14. Annotations are the lazy objects of
  PEP 649 rather than quoted strings: the `from __future__ import
  annotations` of every module goes, the forward references it quoted
  are plain names, and every signature is read lazily, when a
  declaration's sequent is first parsed, so a generator declared
  inside the class its sequent names validates once that class
  exists.
  `pflake8` and `pylint`, each of which reads a lazy forward reference
  as an undefined name, are replaced by `ruff` targeting `py314` — one
  linter, configured in `pyproject.toml` with the same style rules,
  `.pylintrc` deleted — and the CI test matrix runs 3.14 alone.
- One naming convention survives the unification of the generated
  factories with the sequent search: a category's structural classes
  are its capitalised attributes, e.g. `Diagram.Box`, `Ty.Wire` and
  `Arrow.Equation`, built by the `Generator` descriptor unless the
  module declares them, and the snake_case `*_factory` attributes are
  gone — `box_factory`, `swap_factory`, `equation_factory`,
  `generator_factory` and friends, together with
  `monoidal.Box.__init_subclass__`, whose wiring the last generated
  subclass used to clobber. `monoidal.List`'s parameter is named `Atom`,
  as its doctest says.

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
  `Ty`, and `Ty() @ Nat` is refused. The old names are gone with the
  other backward-compatibility shims, see **Removed**
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
- Add a `Functor` attribute to each `Diagram` class and remove
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
- Symmetric categories generate their swaps with `Swap` rather than
  `Braid`, which is now a `classproperty` reading it
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
  `cat.Ob` keeps its name. The old name is gone with the other
  backward-compatibility shims, see **Removed**
  ([#566](https://github.com/discopy/discopy/pull/566)).

### Removed

- Backward compatibility with past DisCoPy versions. The deprecation
  machinery goes — `utils.deprecated_alias` and the module
  `__getattr__`s serving `PRO` for `Nat` and `Ob` for `Wire` — along
  with every shim that read a past version's serialisation: the
  `__setstate__` methods migrating attribute names out of old pickles,
  the `from_tree` branches reading outdated dumps (`cat.Bubble`'s
  singular `'arg'`, `monoidal.Ty`'s `'objects'`, `monoidal.Diagram`'s
  `'boxes'` and `'offsets'`, a plain `cat.Ob` as a wire), the aliases
  `quantum.circuit` kept for pickles from v0.6 — `circuit.Measure`,
  `circuit.Encode` and `circuit.MixedState`, which live in
  `discopy.quantum.gates` — and the cross-version pickle fixtures that
  exercised them. What the current version writes
  reads back, which the `pickling`, `copying` and `serialisation`
  axioms state; what a past version wrote does not.
- `biclosed.Variable` and `closed.Variable` require an atomic codomain:
  the abstraction machinery indexes contexts and free variables by
  variable, counting on that index to coincide with a wire index, so a
  variable of type `x @ y` used to bind only the last wire, leaving the
  other one silently free in `biclosed`, and crash from inside `finset`
  in `closed`, where `Abstraction.eval` permutes as many wires as there
  are free variables
  ([#609](https://github.com/discopy/discopy/issues/609)).
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

- The adjoint of a coloured type keeps its colours, swapped:
  `rigid.Ty.l` and `.r` rebuilt the type from its wires alone, whose
  own adjoints do swap them, so the adjoint of an empty type between
  two equal colours came back transparent and `x.l.r == x` failed on
  it — found by the `adjunction` cell of the matrix.
- `Diagram.to_staircases` runs the identity functor of the diagram's own
  level rather than `monoidal.Functor`, which does not interpret the
  structural bubbles above it: a scalar `Trace` went through the generic
  bubble recursion and came back a plain `Bubble`, so `foliation`
  changed the hypergraph of a diagram with a scalar trace beside
  another scalar box.
- `Diagram.to_hypergraph` records the offsets of the states inside
  merged layers too, where it kept them for staircases only: decoding
  the foliation of two side-by-side states defaulted both to the left
  and reordered them with a swap, so `foliation` was not idempotent.
- A `Feedback` whose memory is on the left draws by tracing on the
  left, keeps its side through `delay` and a functor, and spells it in
  its representation, where it was drawn, delayed, mapped and printed
  as a right feedback. Its equality and hash read `mem` and `left`
  through `setoid`, where a left feedback compared equal to the right
  one on the same argument, its tree records both, where it decoded as
  a right feedback on the default memory, and the functor passes the
  side by calling `feedback_left`, which a stream and a parametric map
  answer with `NotImplementedError` naming their convention where they
  crashed on a keyword they never took. `feedback_left` and
  `feedback_right` peel the outermost memory wire first, so a
  heterogeneous memory of length two or more feeds back where it
  raised `AxiomError` (#606) — the joining law then holds by
  construction, so `feedback.Diagram.feedback_joining` is checked
  again and its counterexample record is gone.
- `Layer.merge` raises `AxiomError` on two layers that compose to the
  identity — a snake whose normal form is empty — which is not a layer
  (#599), where the merge crashed with `UnboundLocalError` reading the
  last layer of an empty loop: the `foliation_soundness` cell of the
  matrix met it on a pivotal diagram.
- `Diagram.foliation` merges the layers of its hypergraph fast path:
  reading the foliation off the hypergraph in one pass over the
  boundary can leave two mergeable layers apart — a state and an
  effect on independent wires — which a second foliation then merged,
  so the foliation was not idempotent. The fast path now runs
  `merge_layers` on what it reads off, which is a fixpoint — found by
  the `foliation_idempotence` cell of the matrix on a Markov diagram
  whose one-legged copy the quotient erases.
- `ribbon.Braid.rotate` of a dagger braid swapped the rotated boundary,
  building the dagger of the rotation of the underlying braid: the
  rotation of `Braid(l, r, is_dagger)` is `Braid(l.r, r.r, is_dagger)`,
  which restores `rotate_contravariance` on ribbon diagrams — found by
  the matrix.
- The representation of a coloured empty type reads back: `biclosed.Ty`
  overrode `__repr__` without the branch that prints a coloured empty
  type as `Ty.id(colour)`, so `rigid.Ty(dom=red, cod=red)` printed as
  `rigid.Ty()` on every level from `biclosed` on — found by the
  `repr_transparency` cells of the matrix. The redundant override goes;
  the bug also exists on `main`.
- `symmetric.Diagram.cycle` refuses a non-atomic wire with a message
  naming it, where `from_permutation` complained about the length of a
  permutation the caller never wrote.
- `para.Closed.curry` defaults `left` to `True` like `abc`, `biclosed`,
  `closed` and `rigid`; every caller passed it explicitly.
- `axioms.levels_of` skips the value parameters of a `NamedGeneric`,
  such as the `dtype` of a tensor diagram, when picking the class whose
  type parameters name the levels, so `tensor.Diagram` and `Circuit`
  find their cells again instead of a single level.
- A rule's method is called through its category rather than looked up
  on the proof of `self`, which may be a plain term of the class the
  rule's category shares a factory with.
- `NamedGeneric.__setstate__` falls back on updating `__dict__` when no
  class below it defines `__setstate__`, fixing `pickle` of a
  parameterised `Matrix`, and pops the legacy values key instead of
  leaving it behind.
- `cat.Arrow.__repr__` reads `self.atom` for box transparency, where
  `self.generator` now names the classmethod declaring a generator.

- Typechecking found four latent crashes: the abstract ``TermBase.eval``
  stub was missing its ``self`` parameter, so ``self.eval()`` typed the
  term as the functor; ``rigid`` raised with
  ``messages.PERMUTATION_HAS_NO_OFFSET``, which was never defined and
  would have crashed with `AttributeError` instead of the intended
  error; an assertion of `Drawing` spelled set union with ``+`` and
  would always have raised `TypeError` had it run; and a
  `closed.Substitution` applied to a `Constant` fell through and
  returned `None`. Substituting under an `Abstraction` still recurses
  forever, left open as future work since fixing it means choosing
  capture semantics. `Merge.dagger` now declares the `Copy` it returns
  and `biclosed.Constant` the string name every caller passes.

- The style review no longer depends on a transition that may never
  happen. `ready_for_review` fires on the draft-to-ready edge alone, so a
  pull request whose `TODO.md` was deleted before it was ever opened went
  unreviewed, silently — no run, no notice, nothing in the Actions tab —
  and a pull request the review did find something on was never reviewed
  again, since fixing a nitpick is a plain push, leaving the correctness
  reviewer, called only on a clean review, never called at all.
  `style-review.yml` now triggers on `opened` and `synchronize` as well: a
  pull request that is not draft and carries no `TODO` file is in the
  review phase by construction, since `no-todo-on-main.yml` forces draft
  while a `TODO` is there, so every revision of it is reviewed. Every
  automatic trigger waits while a `TODO` file is in the tree, which also
  keeps the review from racing that guard — on a `main`-based pull request
  the deleting push lands while the guard still holds it draft, so the
  review comes from the `ready_for_review` that follows rather than twice,
  while a pull request based on anything else, which the guard watching
  `main` alone never drafts and never marks ready, is reviewed on the push
  itself. The hand-over to the correctness reviewer happens once per pull
  request rather than on every clean run, since it re-reviews each push on
  its own. A draft is never reviewed, whatever the trigger, and asking for
  one by comment is what ignores the wait
  ([#615](https://github.com/discopy/discopy/issues/615),
  [#636](https://github.com/discopy/discopy/issues/636)).
- Pickling an instance of a parameterised `NamedGeneric` class silently
  lost the parameter: `__reduce__` stashed the values for a
  `NamedGeneric.__setstate__` that no subclass inherits, since the
  parameterised classes subclass `typing.Generic` instead. A module-level
  reconstructor now parameterises the class before pickle restores the
  state, fixing `pickle` and `copy.deepcopy` of `Hypergraph`, `CMap`,
  `Matrix`, `Tensor`, `interaction.Ty` and `hopf.Representation`, which
  came back with `category` or `dtype` `None` and a stray
  `__class_getitem__values__` attribute
  ([#742](https://github.com/discopy/discopy/issues/742)).
- `rigid.Box` keeps its winding number through `dumps` and `loads`:
  `z` is one of its `serialised_attrs`, where a rotated box used to round-trip
  silently to an unrotated one
  ([#742](https://github.com/discopy/discopy/issues/742)).
- `utils.from_tree` resolves a parameterised factory name such as
  `"tensor.Box[float]"` to its origin class instead of raising
  `AttributeError`
  ([#742](https://github.com/discopy/discopy/issues/742)).
- `Stream[C].sequence` builds a box of `C` rather than a
  `symmetric.Box`, which `Stream.__init__` then wrapped in a `C` diagram
  of one foreign box, since its `box_factory` keyword defaulted to
  `symmetric.Box` whatever the stream was parameterised over. It reads
  `cls.category.Box` and the keyword goes, nothing having passed it.
- Two docs notebooks call attributes that do not exist: the Kauffman
  bracket of `examples.md` reads `Kauffman.Cup`, `Cap` and `Box` where
  the slot rename left it on `cup_factory`, `cap_factory` and
  `generator_factory`, and the cooking example of `diagrams.md` declares
  the objects of its category with `ob` rather than a `ty_factory` that
  never was an attribute, so the annotated `dom` and `cod` of a recipe
  are `Ingredient` rather than a plain `cat.Ob`. No test runs the
  notebooks, only the docs build does.
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
- `rigid.Diagram.Functor` is `rigid.Functor`: it inherited
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
  inherited `Trace` of a user-defined subclass for a class method,
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
- `build.yml` timeouts and a bounded, retried Graphviz install
  ([#591](https://github.com/discopy/discopy/issues/591)).
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
- `Tensor.Spider` returns its array on the active backend instead
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
