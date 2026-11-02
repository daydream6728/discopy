# What property testing has found in DisCoPy

Property testing came to DisCoPy in two waves. The first was discopy/discopy#347, split into the stack discopy/discopy#658–#669 (August–September 2026). It used recursive Hypothesis strategies for diagrams and quotient strategies for `Hypergraph` and `CMap`. The second was rel-int/discopy-next#1 (September–October 2026). It states laws as sequents in `discopy/testable.py` (formerly `discopy/axioms.py`) and derives terms from inference rules (`FreeCategory.search`). Every row below was checked against a commit message, a PR or issue body, a branch's `BUGS.md`, or a `.failing` that was later removed. Rows marked *branch* are fixed only on a branch that has not reached `main`. Bugs found by code reads, review bots, downstream projects or humans are listed under "Not from property testing", even when they sit close to the matrix.

## Found and fixed

| commit | PR / issue | module | law that caught it | bug | class |
|---|---|---|---|---|---|
| ea2c05396 | rel-int/discopy-next#394 | feedback | `dagger_involution`, `rotate_*` on feedback | `Feedback.dagger` and `rotate` crashed with `TypeError` while building an ill-typed diagram that feeds the memory back in time; they now raise `AxiomError`. First seen on discopy/discopy#347 | missing edge case |
| ea2c05396 | rel-int/discopy-next#394 | monoidal | normal form / foliation (regression test `test_identity_spider_in_a_layer`) | `Layer.normalise` kept a layer holding `Spider(1, 1, x)` instead of the type it tensors into | wrong normal form assumption |
| 17cd9e9c9 | rel-int/discopy-next#394 | monoidal | foliation on rigid diagrams | `Layer.merge` raised `UnboundLocalError` on two layers composing to the identity, e.g. a snake; the guard was dropped before the merge as unreachable on `main` | missing edge case |
| ea2c05396 | rel-int/discopy-next#394 | para | `curry_*`, `currying_*` | `para.Compact` curried as a closed category and dropped its coparameters; `para.Closed.curry` silently swallowed them | dispatch/factory |
| ea2c05396 | rel-int/discopy-next#394 | grammar.abstract | copying rule of the search | the copies and discards of abstract diagrams were `closed` functions, not functions of `grammar.abstract` | dispatch/factory |
| ea2c05396 | rel-int/discopy-next#394 | hypergraph | hypergraph laws on `Dim` | the adjoint of a type with no adjoints reversed the shape (`left[::-1]`), so the traced copy of `Dims(Dim(2, 3))` had no hypergraph | coherence |
| ea2c05396 | rel-int/discopy-next#394 | cat, feedback, rigid | `str_transparency` | the `atoms` of delayed boxes, structural boxes and adjoint wires were not the generators their strings name, so `eval(str(x))` failed | serialisation |
| c6dae7e8b | rel-int/discopy-next#395 (review) | feedback | `map_agreement`, `foliation_idempotence` on feedback categories | after a merge, a functor into a traced category (maps) fed a delayed memory to its trace: "Cannot trace a.d with a" | dispatch/factory |
| 05b4f8152 | *branch* | abc | the `Repeat[x, N]` sort of the search | `Nat ** Nat` did not read its exponent with `index`, so the spiders of `Matrix` and `Cospan` could not be built | dispatch/factory |
| 6b1521924 | *branch* | feedback | copying rule of the search | `feedback.Diagram.copy(x, 0)` built a `markov.Discard` that does not compose with feedback diagrams | dispatch/factory |
| 05d9aa7c7 | *branch* | symmetric | `foliation_soundness` on `closed.Diagram` | the identity functor split a native `Permutation` into transpositions, and the hypergraph compares the inside of a curry bubble syntactically | dispatch/factory |
| f1de9c9a9 | rel-int/discopy-next#1 | monoidal | `foliation_idempotence` on Markov diagrams | the hypergraph fast path of `foliation` left two mergeable layers apart (a state and an effect on independent wires) | wrong normal form assumption |
| f8babdaa8 | rel-int/discopy-next#1 | monoidal | adjoint laws on coloured types | the adjoint of a coloured type dropped its colours: `x.l.r` lost the colour of an empty type | coherence |
| f8babdaa8 | rel-int/discopy-next#1, discopy/discopy#347 | monoidal | `foliation` on traced diagrams | `to_staircases` ran the bare `monoidal` identity functor, so a `Trace` became a plain `Bubble` and `foliation` crashed | dispatch/factory |
| f8babdaa8 | rel-int/discopy-next#1 | hypergraph | `foliation_idempotence` | `to_hypergraph` recorded the offsets of states only for staircases, so two side-by-side states came back swapped | wrong normal form assumption |
| 5add76ecb | discopy/discopy#681 | tensor | `serialisation` (types enrolled through the search) | `Dim` had no tree: `dumps(Dim(2, 3))` raised. Also found on discopy/discopy#659 | serialisation |
| 55452c6d8 | rel-int/discopy-next#1 | interaction | laws of the Int-construction | the twist of an integer type raised | missing edge case |
| 0b8fddc84 | rel-int/discopy-next#92 | ehypergraph | `extraction_rewrite` | `rewrite` accepted a right-hand side that identifies boundary positions the region keeps apart, which destroyed a section; it hit 4–14% of drawn e-hypergraphs | missing edge case |
| 648bbd0f2 | rel-int/discopy-next#214 | abc | `test_position` on every enrolled category | `Group` overrode `parameters`, so `position` read a group's arrows as its objects | dispatch/factory |
| 930f11f93 | discopy/discopy#659 | traced, feedback, braided, balanced, markov, frobenius, biclosed, closed | `serialisation`, `transparency` | structural boxes (`Trace`, `Feedback`, `Braid`, `Twist`, `Copy`, `Merge`, `Discard`, `Spider`, `Eval`, `Coeval`, `Curry`) inherited a `repr` or a tree whose `(name, dom, cod)` keys their constructor rejects | serialisation |
| 930f11f93 | discopy/discopy#682 | markov | `pickling` | `markov.Copy.__new__` required an argument that the pickle protocol's bare `__new__(cls)` cannot pass | serialisation |
| 930f11f93 | discopy/discopy#682 | markov, closed | dagger laws on `closed` | `Copy.dagger` and `Merge.dagger` built bare `markov` classes that `closed` diagrams reject | dispatch/factory |
| 1a9a61c10 | discopy/discopy#347 | tensor, monoidal | hypergraph laws on `Dim` and `PRO` | `Dim` and `PRO` hold `int` atoms with no `unwind`, so the hypergraph of any tensor or ZX diagram crashed. Found again independently by humans in discopy/discopy#622 (b8e370785) | dispatch/factory |
| 1a9a61c10 | discopy/discopy#347 | monoidal | `foliation` on pivotal diagrams | `foliation` crashed on boundary-disconnected pivotal diagrams, where `to_hypergraph` is partial; it now falls back to merging layers | missing edge case |
| ac61ed3b2 | discopy/discopy#658 | cat, utils | functor laws into python categories | `Functor._map_atomic` and `utils.is_tuple` recognised only the bare `tuple[type, ...]` alias, not a tuple subclass | dispatch/factory |
| b70da667b | discopy/discopy#660 | hypergraph | equality and `hash` of hypergraphs | `Hypergraph.to_graph` keyed spiders by the boundary's object rather than the spider type, which created a phantom node: `KeyError: 'box'` | coherence |
| d66252f07 | discopy/discopy#661 | matrix | braid laws on `Tensor` | `Matrix.braid = swap` bound the integer `swap`, so `Tensor.braid` skipped `Tensor.swap` | dispatch/factory |
| 89aa309df | discopy/discopy#662 | abc | `pickling` | `NamedGeneric.__setstate__` sat on a class its subscripts never inherit from, so `Matrix[int]` and the like unpickled as their bare origin | serialisation |
| 93885dc7f | discopy/discopy#663 | hopf | ribbon laws on `Intertwiner` | `braid`, `twist`, `cups` and `caps` returned plain dimension boundaries and dropped the module structure | dispatch/factory |
| 29a9dd615 | discopy/discopy#664 | quantum.gates | `transparency` | `Ket` and `Bra` took a bitstring but printed a name | serialisation |
| 29a9dd615 | discopy/discopy#664 | quantum.circuit | `pickling` | `circuit.Box.__setstate__` demanded a `_mixed` key that plumbing such as `quantum.Swap` never stores | serialisation |
| 29a9dd615 | discopy/discopy#664 | quantum.gates | equality laws | `QuantumGate` compares reprs, and `complex(v)` keeps IEEE signed zeros, so `-1j` and `(-0-1j)` compared unequal | numeric |
| da4181344 | discopy/discopy#665 | quantum.zx | `serialisation`, `transparency` | `Spider`, `Scalar` and `H` inherited the `tensor.Box` tree and `repr`. `Scalar` was found by a late, rare draw | serialisation |
| da4181344 | discopy/discopy#665 | quantum.zx | `pickling` | `zx.H` carried a `lambda` as its dagger and could not be pickled | serialisation |
| 5587b1baa | discopy/discopy#667 | python.additive | functor laws | `additive.Function` was missing `@factory`, so its `ar` was the base python `Function` | dispatch/factory |

### Detected, filed, fixed or ruled on later

| commit | PR / issue | module | law that caught it | bug | class |
|---|---|---|---|---|---|
| ac61ed3b2 | discopy/discopy#648, rel-int/discopy-next#142 | cat | `Category.unitality` on `Functor` | `Functor.id() >> F` is not `F`: `MappingOrCallable.then` iterates the keys of the left map, and the identity has none. Fixed by rel-int/discopy-next#322 | coherence |
| 930f11f93 | discopy/discopy#649, rel-int/discopy-next#141 | feedback | `feedback_joining` | `feedback.Diagram.feedback` unrolled its memory in the wrong order, even on homogeneous memory. Fixed by the feedback fold (rel-int/discopy-next#110); 430535f6c on a branch | off-by-one (order) |
| 930f11f93 | discopy/discopy#650, rel-int/discopy-next#140 | monoidal | `transparency` on `Wire` | an uncoloured `Wire` printed as the `cat.Ob` that `Ty` coerces it to, which type-strict equality rejects. Ruled and fixed in rel-int/discopy-next#287 | serialisation |
| b70da667b | discopy/discopy#651, rel-int/discopy-next#139 | hypergraph, cmap | `hypergraph_section`, `map_section` | the decoders need swaps to decode a trace, cup or cap at the traced, balanced and pivotal levels, and `Hypergraph.cups` and `caps` reject left-handed rigid ones. Fixed by rel-int/discopy-next#315 | missing edge case |
| d66252f07 | discopy/discopy#652, rel-int/discopy-next#146 | matrix | `copy_cocommutativity`, `copy_counitality`, `copy_monoidal_coherence` | `Matrix.copy(x, n)` was wrong for `x, n >= 2`; the cells weakened to `Small[C0]` stayed green. Fixed by discopy/discopy#795 | off-by-one |
| 89aa309df | discopy/discopy#653, discopy/discopy#714 | tensor, matrix | `transparency` | `repr` of an array above `NUMPY_THRESHOLD` printed a literal `...`. The law was weakened in rel-int/discopy-next#287 | numeric limit |
| 93885dc7f | discopy/discopy#654, rel-int/discopy-next#145 | hopf | arrow laws, `normal_form`, `serialisation` | `Representation` is a `Dim` carrying an action: `Intertwiner` is not its own factory, its dual cups use dimension reversal, and its trees cannot be decoded | dispatch/factory |
| 93885dc7f | discopy/discopy#655, rel-int/discopy-next#144 | hopf | Reidemeister 1 on `Rep(D(Z/2))` | the pivotal correction fires on a structural comparison of the pivotal element with the unit, so the law fails flakily on `V @ V`. Closed as not planned | coherence |
| da4181344 | discopy/discopy#656, rel-int/discopy-next#149 | quantum.zx | `normal_form` | `zx.Diagram` inherited the `tensor` `spider_factory`, which expects `Dim` rather than `PRO`. Fixed by rel-int/discopy-next#194 | dispatch/factory |
| 4549de8c2 | discopy/discopy#657, rel-int/discopy-next#147 | python.finset | `braid_naturality`, `hexagon_*` | `Function.swap` returned the inverse permutation, which is wrong only when the two halves have unequal lengths. Fixed by f95857423 (rel-int/discopy-next#193) | off-by-one |
| b70da667b | discopy/discopy#713, rel-int/discopy-next#151 | hypergraph, cmap | `serialisation` (all 20 cells) | `Hypergraph` and `CMap` had no `to_tree`. Fixed by de187f5e (rel-int/discopy-next#98) | serialisation |
| 0caed70d4 | discopy/discopy#716 | hypergraph | replaying recorded counterexamples on `Intertwiner` | `Hypergraph.rotate` reversed the ports of each box without swapping them, and did not rotate the spider types. Fixed by discopy/discopy#719 | coherence |
| 93885dc7f | discopy/discopy#718, rel-int/discopy-next#155 | hopf | `foliation_idempotence` | the second foliation of an `Intertwiner` doubled the layers. Later not reproducible on `main` | wrong normal form assumption |
| 6c4e4f13f | rel-int/discopy-next#1 | cmap | every law that reorders disconnected boxes | `CMap` equality depends on the order its boxes are listed in, so the `CMap` strategy is withheld | wrong normal form assumption |
| c53f86d2c | *branch* | compact | `foliation_idempotence` | the hypergraph decoder follows the stored box order, so the foliation of a state feeding an effect through a snake keeps a cut that a second pass straightens. Declared failing | wrong normal form assumption |

### Not from property testing, or uncertain

- 1438ea0a1: a spider of negative arity was accepted. Found by review, not by a cell.
- 237949ea7: a type with no time step is its own delay. A design change that turns inapplicable laws into checked ones; it fixes no bug.
- 4ac9c353f, fb0278b17, 9a4ff14d8, 1f26b7a8d: `make_causal`, the decoder's placement of states (B71), whiskered swaps in functors (B72) and the cap offset (rel-int/discopy-next#187). They come from the code read rel-int/discopy-next#31 and its random-diagram fixtures, not from Hypothesis.
- 76ac2b7d7: rel-int/discopy-next#301. Found through optyx's `unroll`/`double` commutation on rel-int/discopy-next#276.
- 139dff393: a daggered box through a functor whose codomain has no dagger (rel-int/discopy-next#236). Found in optyx.
- c3c09d92c: `Product.__str__` parenthesisation. Found by the review bot cubic on rel-int/discopy-next#47.
- 5df43135d: four `table` defects. Found by an audit against the metatheory carrier.
- b8e370785: `Dim`/`PRO` `unwind` and spider phases, discopy/discopy#622. Prompted by a human; the matrix had found the `unwind` half two months earlier (row 1a9a61c10).
- f0775f300: `@factory` missing on the grammar functors. Fixed by analogy with `additive`; grammar is not enrolled in the matrix.
- The 52-index limit of `numpy.einsum`: discopy/discopy#447, fixed by discopy/discopy#448 (888952776), with the follow-ups discopy/discopy#596 (`opt_einsum` is not declared as a dependency) and discopy/discopy#595 (the greedy path blows up). Found by migrating optyx, whose doubled diagrams exceed 52 wires. 197d01d66 (`to_quimb` labels ≥ 52) and 4be987897 (`Tensor.trace` past 26 factors) came from review. No strategy draws a diagram large enough to reach the limit.
- Bugs the matrix structurally missed, each written up as such in its issue: rotated rigid boxes (rel-int/discopy-next#113: no rule rotates a box), inferred dtypes (rel-int/discopy-next#162: strategies pin the dtype), `python.Ty` transparency (rel-int/discopy-next#165: types were not enrolled), `NamedGeneric` pickling (rel-int/discopy-next#171) and circuit serialisation (rel-int/discopy-next#174: those carriers were not enrolled yet).

## Declared broken

`grep -rn "\.failing(" discopy/` gives 83 hits. 82 of them are declarations; the other is a docstring example in `testable.py`.

| module | count | reasons |
|---|---|---|
| para | 20 | `PARA_REPARAM` (7), `FREE_CURRY` (7), `FREE_FEEDBACK` (4), `PARA_CURRY` (2) |
| feedback | 13 | `NO_PLANAR_NORMAL_FORM` (6, the trace laws), `FEEDBACK_HAS_NO_DAGGER` (3), `FREE_FEEDBACK` (3), `SECTION_NEEDS_SWAPS` (1) |
| biclosed | 12 | `FREE_CURRY` (6), `CURRY_HAS_NO_DAGGER` (3), `NO_PLANAR_NORMAL_FORM` (1), `MAP_OF_A_CURRY` (1), terms do not read back from their tree (1, discopy/discopy#692) |
| rigid | 11 | `NOT_BOUNDARY_CONNECTED` (7), `RIGID_HAS_NO_DAGGER` (3), `SECTION_NEEDS_SWAPS` (1) |
| pivotal | 6 | `FEEDBACK_HAS_NO_DAGGER` (4), `NO_PLANAR_NORMAL_FORM` (2) |
| braided | 5 | `NO_BRAID_GROUP` (3), `FREE_SCALAR` (1), `SECTION_NEEDS_SWAPS` (1) |
| lens | 3 | `LENS_NATURALITY` (2), `LENS_BRAID_NATURALITY` (1) |
| monoidal | 2 | `NO_PLANAR_NORMAL_FORM` (bifunctoriality, dagger monoidality) |
| markov | 2 | `MAP_HAS_NO_SPIDERS`, `STR_SPLITS_LAYERS` |
| closed | 2 | `CURRY_HAS_NO_DAGGER`, `FREE_CURRY` |
| balanced | 2 | `NO_PLANAR_NORMAL_FORM`, `FREE_YANKING` |
| symmetric, stream, spacial, comarkov | 1 each | `FEEDBACK_HAS_NO_DAGGER`, `STREAM_SLIDING`, `FREE_SCALAR`, `MAP_HAS_NO_SPIDERS` |

The 82 declarations fall into four kinds:

- **60 are the checker's incompleteness, not bugs.** The equation of a level cannot decide the law yet:
  - "a hypergraph is faithful only from symmetric categories on, and there is no normal form for this doctrine yet" (`NO_PLANAR_NORMAL_FORM`)
  - "a free curry is a bubble, which a hypergraph keeps as a box" (`FREE_CURRY`, `FREE_FEEDBACK`)
  - "there is no braid group implementation" (`NO_BRAID_GROUP`)
  - parametric maps compared without their reparametrisations (`PARA_REPARAM`)
  - rigid normal forms that need boundary-connected terms (`NOT_BOUNDARY_CONNECTED`)
  - the lens laws, which hold only up to the naturality of copying
- **15 say a structure is absent.** Feedback, curries and rigid cups have no dagger, and the laws are restated with `weaken` on the sub-level that has one. Arguably these should be `inapplicable` rather than `failing`.
- **2 record a design decision.** A closed category cannot curry coparameters (`PARA_CURRY`), the outcome of the `para` fix in ea2c05396.
- **5 are disagreements between encodings that a fix could remove:**
  - a map keeps a copy as a box where a hypergraph merges wires (`MAP_HAS_NO_SPIDERS`, 2)
  - `str` splits a layer of several boxes (`STR_SPLITS_LAYERS`)
  - the map of a curry whiskers a scalar on the other side (`MAP_OF_A_CURRY`)
  - lambda terms do not read back from their tree (discopy/discopy#692)

## Patterns

- **Dispatch and factory bugs are the largest class: 14 of the 35 fixed rows.** Examples are `Matrix.braid = swap`, `Copy.dagger`, a missing `@factory`, `to_staircases`, the native `Permutation`, and the feedback `Discard`. A law written on a base class and checked on every subclass is what exposes a binding that skips the subclass. The search-based derivations of rel-int/discopy-next#1 found most of the later ones: the copying rule (6b1521924, `grammar.abstract`), the `Repeat` sort (`Nat ** Nat`), and enrolled types (`Dim` serialisation).
- **Serialisation comes next: 9 fixed rows and 2 filed ones.** They break `repr`, `str`, tree or pickle round-trips (the structural-box row alone covers 11 classes). Almost all share one cause: a subclass narrows `Box.__init__` and inherits a serialiser written for `(name, dom, cod)`. The serialisation laws are stated once on `Serialisable` and inherited by every enrolled class, so each enrolment catches every such subclass.
- **The conversion laws found the normal-form bugs.** `foliation_idempotence` and `foliation_soundness`, `hypergraph_section` and `map_section` found the offset and ordering bugs in the `Hypergraph` and `CMap` decoders: f8babdaa8, f1de9c9a9, c53f86d2c, and discopy/discopy#651 and #718. The `Hypergraph`/`CMap` quotient strategies of discopy/discopy#660 found the bugs inside the quotient itself: the `to_graph` phantom node, `CMap`'s order-sensitive equality, and the missing trees of discopy/discopy#713.
- **Carrier bugs sit at small edge sizes.** `Matrix.copy` breaks at `x, n >= 2`, `finset.swap` only on halves of unequal length, `QuantumGate` on signed zeros. The matrix found them only after concrete carriers were enrolled, and the `Small[C0]` weakening showed exactly where each law stops holding. These cells have finite support: a green cell says nothing beyond the sizes drawn.
- **Blind spots follow the generators.** Nothing finds what no rule builds: rotated boxes, inferred dtypes, large networks. Every numeric-limit bug, including the 52-index `einsum` limit, came from downstream use (optyx), not from the matrix.
- **Declared-broken cells measure the checker more than the code.** Three quarters of the `.failing` reasons describe what the equation of a level cannot decide yet, and only about five point at a fixable disagreement.

## Found by the sampling experiments

| sampler | module | law | bug | class | status |
|---|---|---|---|---|---|
| `structural_typed`, `structural_perturbed`, `portfolio` | symmetric, compact, frobenius, markov | `str_transparency` | a layer of several boxes prints as `f @ g`, which reads back as two layers: `eval(str(d)) == d` failed. The known `STR_SPLITS_LAYERS`, declared broken on markov only, and failing on frobenius under the default sampler: on symmetric and compact diagrams the default samplers never drew a layer of two boxes, so the cells were green by blind spot | serialisation | fixed: the law compares up to interchange, i.e. the identity functor, which writes each layer as its staircase, and up to the hypergraph on frobenius and neural networks, whose plumbing coalesces on reading back |
| `representational_baseline` | rigid and below | `str_transparency` | a lone rotated box prints as `f.r`, but its atoms were the rotated box, not `f`, so `f` was not in the environment of the law. Smallest counterexample: `Box("f", a, a).r` | serialisation | fixed: `rigid.Box.atoms` unwinds the box, as `Wire.atoms` already did |
| `syntactic_admissible`, `representational_baseline` | closed | `str_transparency` | a closed exponential reads the same on both sides, so `Eval(x >> y)` printed the same on the left and on the right, and a right evaluation read back as a left one. Hidden behind the broken declaration inherited from markov. Smallest counterexample: `Eval(a >> a, left=False)` | printing ambiguity | fixed: a right `Eval` or `Coeval` prints `left=False` |
| `syntactic_baseline` | frobenius | `str_transparency` | tensoring a diagram whose layer holds a spider with one leg on each side merges the spider into the wires around it, leaving a layer with no box, which prints as a bare type. Smallest counterexample: `a @ (Spider(1, 1, b) >> Box('h', b, b))` | missing edge case | fixed: `Diagram.tensor` leaves out a whiskered layer of types only |
| `syntactic_grammatical`, exact, critical | pivotal | none: the experiments' own coherence key | `normal_form` finds that a diagram is not boundary-connected only when `normalize` repeats a step, which takes exponentially many interchanges with several scalars: a 47-layer pivotal diagram of circles ran for over 400,000 rewrites. Small case: `circle @ circle` with `circle = Cap(a, a.r) >> Cup(a, a.r)` cycles at once, three circles and more grow fast | performance | open: checking `Hypergraph.is_boundary_connected` first would fail fast, but would also stop the normal form of a single scalar that `normal_form` gives today |
| `representational_baseline` | every doctrine | a fifth to half of the laws | green cells drawn on 1 to 3 distinct terms (10 of 45 on symmetric diagrams, 32 of 57 on compact ones, in the quick run): the laws with a fixed boundary reject almost everything, yet Hypothesis does not raise `Unsatisfiable` as long as one example is valid. A green cell can be vacuous, which only the distinct count of the report shows | harness | reported by the matrix report as is |
