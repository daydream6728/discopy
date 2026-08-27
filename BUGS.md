# BUGS.md

Every bug the property suite has found so far, grouped by root cause:
most failures were one design flaw repeating across classes, so each group
names the flaw once and lists where it struck. Fixed means fixed on this
branch; open bugs carry their declaration in the matrix.

## Serialisation inherited with the wrong signature

A structural box inherited `__repr__`, `to_tree` or `from_tree` from `Box`
or `Bubble`, whose `(name, dom, cod)` keys its own `__init__` rejects — so
`eval(repr(x))`, `dumps`/`loads` or both crashed on any diagram containing
one. Fixed by giving each class the serialisation its constructor reads.

- `traced.Trace` (repr printed `str` of its argument; no tree at all).
- `feedback.Feedback` (no tree; the memory was not stored).
- `balanced.Twist`, `braided.Braid` (the tree lost `is_dagger`).
- `markov.Copy`, `Merge`, `Discard` (no tree).
- `frobenius.Spider` (no tree).
- `biclosed.Eval`, `Coeval`, `Curry` and their `closed` subclasses
  (repr and tree).
- `quantum.gates.Ket`, `Bra` (repr took a bitstring, printed a name).
- `quantum.zx.Spider`, `Scalar`, `H` (repr and tree; `Scalar` found by a
  late rare draw after the rest were fixed).

## Static bindings where a factory should dispatch

A class attribute captured a concrete sibling instead of reading the
subclass's factory, so every override downstream was silently skipped.
Fixed by dispatching through `cls`.

- `Matrix.braid = swap` bound the integer-typed swap, crashing
  `Tensor.braid` on `Dim`s.
- `Copy.dagger` and `Merge.dagger` built bare `markov` classes, so the
  dagger of a `closed.Copy` was a `markov.Merge` that closed diagrams
  reject — and `closed` had no `Merge` class at all.
- `Diagram.to_staircases` ran the bare `monoidal.Functor`, rebuilding any
  `Trace` as a `monoidal.Bubble` the level rejects, crashing `foliation`
  on every traced diagram.
- `python.additive.Function` missed its `@factory`, so its `ar` resolved
  to the base class of all python functions.
- Open: `zx.Diagram` inherits tensor's `spider_factory`, which expects
  dimensions rather than `PRO` types, so a functor cannot rebuild a ZX
  spider (xfailed in `test_normal_form`).

## Pickling that loses or demands state

- `NamedGeneric.__setstate__` was defined on a class its subscripts never
  inherit from, so every subscripted instance — `Matrix[int]`,
  `Tensor[...]`, `Hypergraph[...]`, `CMap[...]` — unpickled as its bare
  origin class. Fixed by moving the restore into the class they do
  inherit from.
- `markov.Copy.__new__` required an argument the pickle protocol's bare
  `__new__(cls)` call cannot pass, so `Copy` and `Discard` never
  unpickled.
- `quantum.circuit.Box.__setstate__` demanded a mixedness key that
  plumbing like `quantum.Swap` never stores.
- `zx.H` carried a lambda as its dagger, unpicklable by construction; it
  is now a `Hadamard` class that is its own dagger.

## Equality sensitive to representation noise

- `QuantumGate` equality compares reprs, and `complex(v)` keeps IEEE
  signed zeros, so numerically equal gates (`-1j` vs `(-0-1j)`) compared
  unequal. Fixed by normalising the zeros on construction.
- `Hypergraph.to_graph` keyed spider nodes by the boundary's object
  rather than the spider's own type, creating a phantom attributeless
  node whenever a boundary wire reads an adjoint of its spider type —
  `hash` crashed with `KeyError: 'box'`.

## Type atoms that are not wires

`Dim` and `PRO` store bare integers where the type machinery expects
`Wire`-like atoms, so every generic path that walks atoms crashed.

- `Dim` had no tree serialisation and no `unwind`, crashing `dumps` and
  the hypergraph of any tensor diagram.
- `PRO` likewise had no `unwind`; and its constructor silently drops the
  colours it accepts, so its coloured `identity_typing` is declared
  inapplicable rather than fixed.
- `Functor._map_atomic` and `utils.is_tuple` only recognised the bare
  `tuple[type, ...]` alias, so a tuple-subclass `ob` (the python
  carriers' `Types`) made functors into python categories iterate a bare
  type.

## An object discipline torn between modules and dimensions

`hopf.Representation` is a `Dim` carrying an action, and the code mixes
the two freely: generic diagram operations slice modules down to bare
dimensions by design, while the module structure is needed wherever an
action is read.

- Fixed: the ribbon classmethods `Intertwiner.braid`, `twist`, `cups`
  and `caps` returned plain dimension boundaries, dropping the module
  structure their callers read the action from.
- Open: `Intertwiner` is not its own factory — its `ar` resolves to the
  plain tensor category, and making it one cascades into every generic
  operation that builds dimension-boundaried composites — so the
  arrow-quantified laws are declared inapplicable.
- Open: the hypergraph functor rebuilds a representation-typed cup or
  cap whose adjoint is its dimension reversal, not the dual module, so
  `normal_form` and `foliation` cannot be checked up to hypergraph.
- Open: a class subscripted by an algebra instance has no importable
  factory name, so its trees cannot be decoded.

## Partial operations that crashed instead of degrading

- `foliation` crashed where `to_hypergraph` is partial — traced diagrams
  (via `to_staircases` above) and boundary-disconnected pivotal diagrams,
  whose rejection is by design; it now falls back to merging layers.
- `Feedback.dagger` crashed with a `TypeError` from generic bubble
  reconstruction; it now raises a clean `AxiomError`, the delay being
  irreversible.

## Open, declared and recorded in the matrix

- `Matrix.copy(x, n)` is wrong for `x, n >= 2` (#606): recorded in the
  counterexample ledger; the weakened cells prove cocommutativity and
  counitality green below dimension two, while the monoidal coherence
  reaches dimension two even from atomic arguments.
- `finset.Function.swap` returns the inverse permutation (#606): correct
  only where both halves have equal length, a joint constraint
  per-argument generation cannot state.
- `feedback.Diagram.feedback` unrolls its memory in the wrong order
  (#606), falsified even on homogeneous memory.
- `CMap.to_diagram` and `Hypergraph.to_diagram` need swaps to decode a
  trace, cup or cap at `traced`, `balanced` and `pivotal`, and
  `Hypergraph.cups`/`caps` accept only the right-adjoint orientation, so
  `to_hypergraph` is partial on rigid's left-handed cups and caps.
- Reidemeister 1 fails semantically on a composite module of
  `Rep(D(Z/2))`, recorded in the ledger on `V @ V`: the swap is the
  braiding, and the pivotal correction of cups and caps fires on a
  *structural* comparison of the pivotal element with the unit —
  semantically equal but structurally distinct composites — flakily,
  since the rebuilt dual actions compare structurally unstably.
- An uncoloured `monoidal.Wire` reprs as the `cat.Ob` that `Ty` coerces,
  which its type-strict equality rejects.
- A `Tensor` with more than `config.NUMPY_THRESHOLD` entries elides its
  repr as a literal ellipsis, breaking transparency.
