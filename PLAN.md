# Shapes as finitely presented categories

A redesign of the property-testing infrastructure of
[discopy/discopy#658](https://github.com/discopy/discopy/pull/658): the
argument shapes (`ComposablePair`, `Square`, `TraceDinaturality`, ...)
become finite presentations of categories, the axioms become their
relations, and instance generation becomes one generic functor into the
Kleisli category of the `SearchStrategy` monad. Cyclic imports between
`testing`, `abc` and the concrete modules are assumed solvable and set
aside; the last section records where the cycles actually are.

## The idea in one paragraph

In #658 every axiom is a Python function whose annotated parameters name a
bespoke `Strategy` wrapper class, and every wrapper hand-codes its own
chain of dependent Hypothesis draws — `PastingDiagram.strategy` pads
columns with identities, `TraceSliding.strategy` wires four drawn objects
into two boundary constraints, and so on for ~500 lines. But each of these
wrappers is secretly the same thing: a finite presentation of a category —
finitely many generating objects, finitely many generating arrows with
typed boundaries — and generating its arguments is secretly the same
algorithm: draw an image for each generating object, then an image for
each generating arrow with the boundary the object images determine. That
algorithm is a functor from the shape to the Kleisli category of
`SearchStrategy`, where sequential composition *is* dependent drawing. An
axiom, in turn, is a relation of the presentation: a pair of formal
composites of the generators that a carrier must identify. One data
structure, `Presentation`, and one generic `instances` replace every
wrapper class and every per-shape `strategy` method; a cell of the
property matrix becomes "draw a functor from the shape to the carrier,
evaluate the relation's two sides through it, compare with the carrier's
`equation_factory`".

## The mathematical picture

### `Search`, the Kleisli category of the strategies monad

`hypothesis.strategies.SearchStrategy` is a strong commutative-enough
monad on Python types: `st.just` is the unit, `.flatmap` is the bind,
`.map` is the functor and `st.tuples` is the monoidal strength. Its
Kleisli category `Search` has Python types as objects and functions
`A -> SearchStrategy[B]` as arrows `A -> B`:

- **composition** `f >> g` is `lambda a: f(a).flatmap(g)` — draw, then
  draw depending on the result: exactly the dependent generation every
  bespoke `strategy` method writes by hand today;
- **tensor** `f @ g` draws independently, via `st.tuples`;
- **copy** duplicates a drawn *value* (not the strategy — the two copies
  share one sample) and **discard** forgets one, so `Search` is a Markov
  category, an instance of `abc.MarkovCategory` like
  `python.multiplicative.Function` is of closed structure. Copying is not
  natural — `copy >> (f @ f)` shares a draw where `f >> copy` repeats one
  — which is precisely the Markov, not cartesian, signature of
  nondeterminism.

DisCoPy eats its own dogfood here: the generation schedule of a shape is
itself a string diagram, evaluated in `Search`, and `Search` can carry the
usual tests of a concrete category.

### Shapes are finite presentations, instances are functors

A **shape** is a finite presentation of a category in a doctrine — a
level of `discopy.abc`: some generating objects (*colours*), some
generating arrows with boundaries that are object terms over the colours
(words, but also delays, duals or exponentials where the doctrine has
them), and some **relations**, formal equations between composites of the
generators under the doctrine's operations.

An **instance** of a shape `S` in a carrier `C` is a functor from the free
category on `S`'s signature to `C` — and DisCoPy already implements
exactly this functor: the signature is presented with the free module of
the doctrine (`cat.Box`, `monoidal.Box`, `traced.Box`, ...), an instance
is a finite `ob_map`/`ar_map`, and evaluation is the module's own
`Functor`. Functors are what make the arity plumbing disappear: a colour
is atomic in the shape, but its image is an arbitrary carrier object, and
`traced.Functor` already knows that tracing one shape wire means tracing
`len(F(u))` carrier wires. The `C0`/`C1` type variables, the `eval` of
string annotations, the PEP 695 scope workaround and the
`from __future__ import annotations` requirement of #658 all become
unnecessary: instantiation is functor application, not annotation
rebinding.

The **axiom** is the relation: `C` satisfies it iff every instance
functor identifies its sides, i.e. iff every functor from the free
signature factors through the presented quotient. This is the classical
picture — presentation, model, satisfaction — and the property matrix is
its finite search: `carrier |= shape` sampled over instances.

### Strategies are functors into `Search`

A carrier's generation data is two kernels:

- `1 -> Ob`: draw an object, `carrier.ob.strategy()`;
- `Ob @ Ob -> Ar`: draw an arrow with a given boundary,
  `carrier.strategy(dom=..., cod=...)`.

That is, *a carrier together with its strategies is a category internal
to the Markov category `Search`*. The strategy of a shape `S` is then the
functor it induces into `Search` — concretely, into coparameterised
kernels, `para.Symmetric` over `Search` with its coparameter space (the
codebase already has coparameters, #572):

- each colour goes to the space of carrier objects;
- each generating arrow `f : w -> v` goes to the kernel that reads the
  colour images, evaluates the boundary terms, draws an arrow on that
  boundary, and emits the drawn arrow as a coparameter;
- composition in the shape goes to Kleisli composition — drawing a
  composable pair *is* the composite of two kernels, the intermediate
  boundary passed along the wire — and tensor goes to independent draws.

Generating a full instance evaluates this functor on a foliation of the
shape: colours first (a tensor of independent draws), then the generators
in any order (they depend only on the colour images), the coparameters
accumulating into the finite `ar_map`. `ComposablePair.strategy`,
`PastingDiagram.strategy`, `TraceSliding.strategy` — all of them are this
one evaluation on different presentations. The identity-padding of
`PastingDiagram` disappears entirely: a functor from the walking square
already *is* four arbitrary carrier arrows with matching boundaries,
because the shape's typing carries the constraint.

### The third gotcha: relations live one level of freeness up

The free modules already satisfy their own axioms: `cat.Arrow` composes
by list concatenation, so `(f >> g) >> h == f >> (g >> h)` *in the
shape*, and a relation stated as two free arrows would evaluate to the
same carrier program twice — a trivially green cell. (Interchange is
safe: `monoidal.Diagram` is premonoidal, `f @ c >> b @ g` and
`a @ g >> f @ d` are distinct diagrams. Associativity, unitality, the
typing laws and the monoid laws of `Ty` are not: verified on `main`,
`(f >> g) >> Id(z) == f >> (g >> Id(z))` and `(a @ b) @ c == a @ (b @ c)`
hold strictly.)

So the two sides of a relation are stated in `Term`, the absolutely free
syntax over the shape's generators: a tree of doctrine operations, built
with the same operators as diagrams (`>>`, `@`, `.trace()`, `.curry()`,
`.dagger()`, `.feedback()`, `.dom`, `.cod`, `Term.id`, `Term.swap`, ...)
but left unevaluated, and folded through an instance functor by
`Term.eval`: leaves map through the functor, operations through the
carrier's own methods, so the two sides run as two genuinely different
carrier programs. A free diagram embeds as the leaf `Term(diagram)`,
evaluated as `functor(diagram)`, for the sides where the free module
does distinguish them.

## The interface

Everything below lives in `discopy/testing.py` (with the shapes possibly
in a sibling `discopy/testing/shapes.py`); signatures only, bodies
elided.

```python
@dataclass
class Search:
    """
    A morphism of the Kleisli category of the ``SearchStrategy`` monad:
    ``inside`` maps ``len(dom)`` drawn values to a strategy on
    ``len(cod)``-tuples. An instance of :class:`abc.MarkovCategory`.
    """
    inside: Callable[..., st.SearchStrategy]
    dom: tuple[type, ...]
    cod: tuple[type, ...]

    @classmethod
    def id(cls, dom): ...              # st.just
    def then(self, other): ...         # flatmap
    def tensor(self, other): ...       # st.tuples, independent draws
    @classmethod
    def copy(cls, x, n=2): ...         # share one draw
    def draw(self): ...                # the schedule is a string diagram


@dataclass(frozen=True)
class Term:
    """
    A formal composite of shape generators under doctrine operations —
    the absolutely free syntax the two sides of a relation are stated
    in, since the free modules already normalise their own axioms.
    """
    operation: str      # "leaf", "id", "then", "tensor", "trace", ...
    arguments: tuple

    def then(self, other): ...
    def tensor(self, other): ...
    def trace(self, wires, left=False): ...   # wires an object Term
    def curry(self, n=1, left=True): ...
    def feedback(self, mem): ...
    def dagger(self): ...
    dom = property(...)                # object Terms, for typing laws
    cod = property(...)
    __rshift__, __matmul__ = then, tensor

    def eval(self, functor):
        """Fold the operations through the carrier of the functor."""


@dataclass
class Presentation(NamedGeneric["category"]):
    """
    A finite presentation of a category in the doctrine of ``category``,
    a free module: generating objects read off the generators' boundaries
    plus explicit extra ``colours``, generating arrows as free boxes, and
    relations as equations between Terms over the generators.
    """
    generators: tuple[Box, ...]
    relations: tuple[Equation, ...] = ()
    colours: tuple = ()

    def relate(self, *relations) -> Presentation:
        """The same signature with relations (re)stated."""

    def instances(self, carrier, params=None) -> st.SearchStrategy[Functor]:
        """
        The canonical strategy on functors from the free category on the
        signature to the carrier: one draw per cell of the presentation,
        Kleisli-composed in :class:`Search` — colours from
        ``carrier.ob.strategy()``, each generator from
        ``carrier.strategy(dom=..., cod=...)`` on the boundary the colour
        images determine. ``params`` maps a generator (or a colour) to
        keyword constraints forwarded to its draw.
        """

    def check(self, carrier, functor) -> tuple[Equation, ...]:
        """Each relation evaluated through the instance, one carrier
        equation per relation, built with ``carrier.equation_factory``."""

    def __matmul__(self, other): ...   # disjoint union: independent draws
    def glue(self, other, **identify): ...  # pushout along shared colours


@dataclass
class Axiom:
    """
    A shape bound to a carrier by inheritance — the descriptor of #658
    with the equation function replaced by a Presentation. The matrix
    ids, ``failing``, ``inapplicable``, ``modulo`` and the record format
    keep their semantics.
    """
    shape: Presentation

    def strategy(self): ...            # shape.instances(carrier, params)
    def __call__(self, functor): ...   # shape.check, or NotImplemented
    def falsify(self, **params): ...   # hypothesis.find over instances
    def modulo(self, up_to): ...
    def failing(self, reason): ...
    def inapplicable(self, reason): ...
    def weaken(self, **params): ...    # per-generator draw constraints
```

What a carrier must provide shrinks to the two terminal strategies #658
already has — `Ob.strategy`, `Box.strategy`, `Arrow.strategy(dom=, cod=)`
and their overrides down the hierarchy — everything above them goes
generic. Applicability becomes mostly derivable: a shape presented in the
traced free module applies to a carrier iff the carrier implements
`abc.TracedCategory`, so most `inapplicable` declarations follow from the
doctrine instead of being stated by hand (a few stay manual, e.g.
`serialisation` on `Natural`).

## Defining shapes and axioms: worked examples

### `cat`: composition and its typing

```python
from discopy import cat
from discopy.abc import Equation
from discopy.testing import Axiom, Presentation, Term

x, y, z, w = map(cat.Ob, "xyzw")
f, g, h = cat.Box('f', x, y), cat.Box('g', y, z), cat.Box('h', z, w)
f_, g_, h_ = map(Term, (f, g, h))

ComposablePair = Presentation[cat.Arrow](generators=(f, g))
ComposableTriple = Presentation[cat.Arrow](generators=(f, g, h))

Unitality = Presentation[cat.Arrow](generators=(f, )).relate(
    Equation(Term.id(f_.dom) >> f_, f_, f_ >> Term.id(f_.cod)))
Associativity = ComposableTriple.relate(
    Equation((f_ >> g_) >> h_, f_ >> (g_ >> h_)))
CompositionTyping = ComposablePair.relate(
    Equation((f_ >> g_).dom, f_.dom), Equation((f_ >> g_).cod, g_.cod))
DaggerInvolution = Presentation[cat.Arrow](generators=(f, )).relate(
    Equation(f_.dagger().dagger(), f_))
```

and on the abstract base class the axioms are one line each:

```python
class Category(ABC):
    unitality = Axiom(Unitality)
    associativity = Axiom(Associativity)
    composition_typing = Axiom(CompositionTyping)
    dagger_involution = Axiom(DaggerInvolution)
```

with the classifications of #658 unchanged in form:

```python
class Functor(Category, ...):
    unitality = Category.unitality.failing(
        "Composition is unital only on the left: ... (#658)")
```

### `monoidal`: the monoid laws and interchange

The monoid laws of `Ty` are a presentation whose carrier is the monoid
itself — an instance is just a choice of images for the colours, and
`ColouredMonoid` states them once for every `Ty`-like carrier:

```python
from discopy import monoidal

a, b, c, d = map(monoidal.Ty, "abcd")
a_, b_, c_, d_ = map(Term, (a, b, c, d))

MonoidUnitality = Presentation[monoidal.Ty](colours=(a, )).relate(
    Equation(Term.unit() @ a_, a_, a_ @ Term.unit()))
MonoidAssociativity = Presentation[monoidal.Ty](colours=(a, b, c)).relate(
    Equation((a_ @ b_) @ c_, a_ @ (b_ @ c_)))
```

Interchange is the walking pair of horizontally separated arrows — two
generators, no grid, no identity padding, because a functor image of `f`
is already an arbitrary carrier arrow:

```python
f, g = monoidal.Box('f', a, b), monoidal.Box('g', c, d)
f_, g_ = Term(f), Term(g)

Interchange = Presentation[monoidal.Diagram](generators=(f, g)).relate(
    Equation((f_ @ c_) >> (b_ @ g_), f_ @ g_, (a_ @ g_) >> (f_ @ d_)))
```

`Square` survives only where a law genuinely needs four cells, as the
gluing `ComposablePair.glue(ComposablePair, ...)` or a direct
four-generator presentation — but interchange itself no longer does.

### `symmetric`: naturality of the swap

Structural morphisms of the doctrine appear as `Term` operations on
object terms, so a shape can mention swaps of colours whose images are
arbitrary objects:

```python
from discopy import symmetric

a, b, c = map(symmetric.Ty, "abc")
f = symmetric.Box('f', a, b)

SwapNaturality = Presentation[symmetric.Diagram](
    generators=(f, ), colours=(c, )).relate(
        Equation((Term(f) @ c_) >> Term.swap(b_, c_),
                 Term.swap(a_, c_) >> (c_ @ Term(f))))
```

### `traced`: vanishing and dinaturality

`Term.trace` takes an object term rather than an integer, and the
instance functor supplies the arity: tracing the colour `u` in the shape
means tracing `len(F(u))` wires in the carrier — including zero, so the
vanishing axiom of #578 is one relation:

```python
from discopy import traced

u, v, x, y = map(traced.Ty, "uvxy")
u_, v_, x_, y_ = map(Term, (u, v, x, y))
f = traced.Box('f', x, y)

TraceVanishing = Presentation[traced.Diagram](generators=(f, )).relate(
    Equation(Term(f).trace(Term.unit()), Term(f)))

f, g = traced.Box('f', x @ u, y @ v), traced.Box('g', v, u)
TraceDinaturality = Presentation[traced.Diagram](
    generators=(f, g)).relate(
        Equation((Term(f) >> (y_ @ Term(g))).trace(u_),
                 ((x_ @ Term(g)) >> Term(f)).trace(v_)))
```

`TraceSliding`, `TraceNaturalityLeft/Right`, `TraceDinaturalityLeft/Right`
and `TraceSuperposing` are each a presentation of this size; the four
drawn objects and two boundary equations their `strategy` methods wire by
hand are the shape's typing, enforced by the generic `instances`.

### `closed` and `feedback`

```python
from discopy import closed, feedback

e = closed.Ty('e')
f = closed.Box('f', a @ e, b)
CurryUncurry = Presentation[closed.Diagram](generators=(f, )).relate(
    Equation(Term(f).curry().uncurry(), Term(f)))

s, m, n = feedback.Ty('s'), feedback.Ty('m'), feedback.Ty('n')
m_, n_ = Term(m), Term(n)
f = feedback.Box('f', s @ (m @ n).delay(), s @ (m @ n))
FeedbackJoining = Presentation[feedback.Diagram](generators=(f, )).relate(
    Equation(Term(f).feedback(m_ @ n_),
             Term(f).feedback(n_).feedback(m_)))
```

The boundary of `f` uses `delay()` on an object term over the colours:
boundaries are object terms evaluated under the partial functor, so
`FeedbackJoining.instances` draws `F(m)`, `F(n)`, then an arrow on
`F(s) @ (F(m) @ F(n)).delay()` — the checks `FeedbackJoining.__new__`
does by hand today, for free.

### `Cat` itself: laws of elements become laws of a carrier

The `self`-receiver machinery of #658 (`is_method`, the synthesised
receiver parameter) dissolves: a law about functors is an ordinary shape
checked in the carrier `Cat`, whose object strategy is (essentially)
`st.just(cls.dom)` and whose hom strategy is the `Relabelling`-based
`Functor.strategy`. An instance of `ComposablePair` in `Cat` is a pair of
composable functors, and `Functor.unitality` is the same `Unitality`
shape as everywhere else — with the same `.failing` declaration for the
known one-sidedness of `MappingOrCallable.then`.

The per-element laws that are not equations in a category —
`transparency`, `pickling`, `serialisation` — stay as they are in #658:
they are laws of representation, not of structure, and gain nothing from
a shape.

### Subspaces, quotients, records

- `weaken` constrains draws instead of wrapping arguments:
  `Interchange.axiom.weaken(f=dict(boundary_connected=True))` forwards
  the keyword to that generator's `carrier.strategy` call — categorically
  a restriction of the strategy functor along a sub-presentation. The
  membership-validating wrappers (`Atomic`, `NonEmpty`, `Subsingleton`,
  `BoundaryConnected`) become draw parameters (`max_length=1`,
  `min_length=1`, `boundary_connected=True`).
- `modulo` is unchanged: it still rebinds `up_to` on the checked
  `Equation`, and `equation_factory` still lets a carrier quotient all
  its equations at once.
- A recorded counterexample becomes *one* transparent object — the
  instance functor, a finite mapping over the shape's generators —
  instead of a tuple of ad-hoc wrappers:

  ```python
  Counterexample(
      axiom=Functor.unitality,
      functor=cat.Functor(ob_map={...}, ar_map={...}),
      reason="Composition is unital only on the left (#658).")
  ```

  which pickles, reprs and replays uniformly, whatever the shape.

## What this deletes

| #658 | becomes |
| --- | --- |
| `PastingDiagram` + `ComposablePair/Triple`, `HorizontalPair`, `Square` | four presentations, a few lines each |
| `TraceSuperposing`, `TraceSliding`, `TraceNaturality*`, `TraceDinaturality*` | five presentations |
| `LeftCurrying`, `RightCurrying` | two presentations |
| `FeedbackVanishing/Joining`, `HomogeneousMemory` | three presentations (homogeneity a draw constraint) |
| `Atomic`, `NonEmpty`, `Subsingleton`, `BoundaryConnected` | draw parameters of the carrier strategies |
| `Axiom.strategy`'s annotation `eval`, `C0`/`C1` rebinding, `substitute`, the PEP 695 `locals` workaround | functor application |
| `Axiom.is_method`, the synthesised receiver | the `Cat` carrier |
| per-shape hand-rolled `@st.composite`/`flatmap` chains | one generic `Presentation.instances` |

Kept: the terminal strategies (`Ob`, `Box`, `Arrow` and their overrides —
the only genuinely carrier-specific generation), `Natural` and
`Relabelling` (headed to the main library per upstream #709/#711), the
`Equation` of `abc`, the classification combinators, the matrix, records,
profiles and CI of `proptest/`. Net effect on `discopy/testing.py`:
roughly half its 1200 lines replaced by ~150 lines of `Search`/`Term`/
`Presentation` plus declarative shape definitions.

## Implementation plan

0. **Baseline.** Merge upstream #658 into this branch; the suite is the
   safety net for the refactor.
1. **`Search`** (~100 lines + tests): the Kleisli category as a Markov
   category, with its own unit tests and a doctest drawing a generation
   schedule.
2. **`Term`** (~120 lines + tests): the operation table (one entry per
   doctrine operation), `eval` by structural recursion, `repr`
   transparency.
3. **`Presentation` + generic `instances`** (~150 lines): colours,
   boundary evaluation, topological draw order, functor assembly; port
   the `cat`-level axioms of `abc.Category`/`ColouredMonoid` and delete
   `ComposablePair`/`ComposableTriple`; the matrix must stay green on
   `cat.Arrow` and `cat.Functor` (same cells, same expected failures).
4. **Port the upper hierarchy**: interchange, swap naturality, the trace,
   currying and feedback shapes; delete the bespoke classes; check reach
   with `assert_strategy_finds` unchanged.
5. **Subspaces and records**: `weaken` as draw constraints, records as
   functors, migration of any recorded counterexamples.
6. **Docs and audit**: rewrite the module docstring's protocol around
   presentations; run the strategy audits (reach, rarity, observation) to
   confirm the generic generator finds the bugs the bespoke one did —
   in particular re-falsify `Functor.unitality`.

## Open questions

- **Shrinking quality.** Hypothesis shrinks through `flatmap` chains less
  effectively than through a flat `@st.composite`; if shrunk instances
  get worse, `instances` can compile the same schedule to one composite
  block — the functor is the spec, the compilation an optimisation.
- **Distribution vs the bespoke strategies.** `PastingDiagram` biased its
  draws (identity padding, `n_active_rows`); the generic generator is
  uniform over the presentation. Rarity audits will say whether any shape
  needs per-generator weights in `params`.
- **Which relations may stay diagrams.** Any side the free module
  distinguishes could be a plain diagram leaf; the conservative rule —
  always `Term` — costs a little syntax but can never silently trivialise
  a cell. Worth revisiting once `Term` exists.
- **The actual import cycles**, assumed away here: `testing` needs the
  free modules to present shapes, `abc` needs `testing.Axiom`, and every
  free module imports `abc`. Candidate resolutions, for a later stage:
  declare shapes lazily (a thunk evaluated at first `instances`), move
  the shape definitions to a module imported late
  (`discopy/testing/shapes.py`), or declare axioms on the concrete
  modules rather than on `abc` and inherit them the same way.
