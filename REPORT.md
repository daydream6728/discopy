# Report: DisCoPy's data structures as frozen dataclasses

Branch `experiment/frozen-dataclasses`, cut from rel-int/discopy-next `main`
at `723e7690`. Everything below was run on one machine (macOS, Apple
silicon, Python 3.14.5). Commits are local to that branch.

## Summary

- **The hypothesis holds.** Once a box declares the data it is built
  from as fields, `replace` rebuilds it with the other fields kept. All
  eight broken cases pass, and so do the rebuilds the levels above carried
  by hand. `subs`, `lambdify`, `dagger`, `delay` and `setoid` are each
  written once, in `cat` or `feedback`, over the fields. The four ad hoc
  rebuild schemes the code had go away:
  - `type(self)(name, dom, cod, ...)` in `cat`;
  - feedback's recorded constructor call (`_args`, `_params`);
  - markov's `flagged`, which mutated a rebuilt box to copy its flags;
  - `__getnewargs__` read by `delay`.
- **Plain `@dataclass` does not compose with the hierarchy.** It needs
  two pieces of machinery, both in `utils` (about 100 lines):
  1. *Diamonds lose fields.* `dataclass` reads each base's fields with
     `getattr`, so a class that is not decorated inherits only the fields
     of the first decorated base in its MRO. 107 classes dropped fields
     that way, e.g. `pivotal.Box` lost `time_step` and every `zx` box
     lost `z`. `inherit_fields` runs from `__init_subclass__` of `cat.Ob`
     and `cat.Arrow`. It merges the fields of all bases, taking each one
     from the nearest base that has it.
  2. *Fields added by one level leak into every structural class below
     it.* `time_step`, `z`, `deterministic`, `affine` and `is_mixed`
     reach `Swap`, `Spider`, `Feedback` and the rest, whose constructors
     do not take them. Marking each of them `init=False` in every class
     does not scale. Instead `inherit_fields` takes as constructor
     fields exactly those the class's `__init__` has a parameter for,
     unless it takes `**kwargs`.
- **Frozen is where most of the cost is.** Every constructor that
  assigns a field had to go through `object.__setattr__` (64 call sites
  of `utils.setattrs`). The drawing code, which styles boxes by
  assignment, had to change too. Decorating a class freezes its exact
  instances against *any* assignment, so styling a box after
  construction now works on some classes and not others. Pylint cannot
  see fields set this way and drops to 9.08 (from 9.16).
- **Cost in time:** the benchmarks of `benchmark/` are 7% slower (geometric mean), none of them by more than 25% once the two hottest constructors set their fields inline; before that, composing diagrams in series was up to 46% slower.
- **Recommendation:** propose the *fields* upstream, in four small slices,
  and keep *frozen* out until the drawing stops mutating boxes. See the
  last section.

## What converted

`@frozen` is `dataclass(frozen=True, init=False, eq=False, repr=False)`
followed by `inherit_fields`. A *derived* field is computed by the
constructor rather than taken (`init=False`), so `replace` does not give
it back. A *property-backed* field is declared but read through a
property, so its value is never stored twice.

| Class | Fields it is built from | How |
|---|---|---|
| `cat.Ob` | `name` | `@dataclass(frozen=True, repr=False)`: generated `__init__`, `__eq__` and `__hash__`, check in `__post_init__` |
| `cat.Arrow` | `inside, dom, cod` | `@frozen`, hand-written `__init__` (`_scan` is an instruction) |
| `cat.Box` | `name, dom, cod, data, is_dagger` | `inside` derived and not compared (the cycle) |
| `cat.Sum` | `terms, dom, cod` | `name, data, is_dagger` derived, hand-written `__replace__` |
| `cat.Bubble` | `args, dom, cod, name, method` | `data` and `is_dagger` not compared, as before; cooperative `__init__`; takes `args=` |
| `monoidal.Ty` | `inside, dom, cod` | `name` derived, own `__eq__` |
| `monoidal.Layer` | `boxes_or_types` | hand-written `__replace__`: `normalise` is an instruction, so `replace` re-normalises |
| `monoidal.Diagram`, `monoidal.Box` | inherited | decorated so that their instances are frozen |
| `monoidal.Bubble` | `+ drawing_name, draw_as_frame, draw_as_square, draw_vertically` | not compared |
| `feedback.Box` | `+ time_step` | replaces `_args` and `_params` |
| `feedback.Feedback`, `Trace` | `arg, dom, cod, mem, left` | `arg` property-backed (`Bubble.arg`) |
| `feedback.Head`, `Tail`, `FollowedBy` | `arg, time_step` (`+ is_dagger`) | |
| `markov.Box` | `+ deterministic, affine` | the constructor still takes `is_deterministic` and `is_affine`; `flagged` deleted |
| `rigid.Box` | `+ z` | `rotate` and `dagger` via `replace` |
| `pivotal.Box` | join of `rigid.Box` and `feedback.Box` | hand-copied `rotate` and `dagger` replaced |
| `biclosed.Curry` | `arg, n, left` | `closed.Curry` spells out `(arg, n, left, time_step)` because `Timed` hides it behind `*args, **params` |
| `biclosed.Eval`, `Coeval` | `x, left` | same for the closed ones |
| `tensor.Bubble` | `+ func` | `*args` rather than `inside`, so `replace` can give `args` back |
| `tensor.Box.setoid` | | derived from the compared fields rather than listed by hand |
| `frobenius.Spider` | `n_legs_in, n_legs_out, typ, data` | stored; `name, dom, cod, deterministic, affine` explicitly derived because of `**params` |
| `zx.Spider` | `n_legs_in, n_legs_out, phase` | `phase` property-backed |
| `circuit.Box` | `+ is_mixed` | replaces `_is_mixed`, a property and a `_params` patch; gates pass `is_mixed=False`; `Permutation` and `Sum` compute it |
| `gates.Rotation` | `phase, z, time_step` | `phase` stored, rather than kept in `data` behind a property |
| `gates.Scalar`, `MixedScalar`, `Sqrt` | | overrides that compensated for the lossy rebuild deleted |
| `gates.Controlled` | `controlled, distance` | |
| `utils.BinaryBoxConstructor` | `left, right` | gives them to `Braid`, `Cup`, `Cap` and the crossed compositions |
| `symmetric.Permutation` | `dom, perm` | `perm` stored as `finset.Permutation`, which the constructor accepts back |
| `symmetric.Swap` | `left, right` | own `__new__(left, right)`: the inherited `Permutation.__new__(dom, perm)` refused the keywords |
| `markov.Copy`, `comarkov.Merge` | `x, n` | property-backed: views of the boundary |
| `markov.Function`, `comarkov.Cofunction` | `dom, func` / `cod, cofunc` | the constructor accepts its own field back |
| `frobenius.Cospan` | `apex, left, right` | `left, right` property-backed (`legs`) |
| `balanced.DualRailBraid`, `ribbon.DualRailCup`, `DualRailCap` | `left, right` | |

### The probe's list of constructors that do not store what they take

| Constructor | Decision | Why |
|---|---|---|
| `Swap(left, right)` | fields `left, right`; `name, dom, cod` derived | the generating data is what the box is |
| `Copy(x, n)`, `Merge(x, n)` | fields read from the boundary | storing them would duplicate `dom` and `cod` |
| `Spider(n_legs_in, n_legs_out, typ, data)` | fields stored | `typ` cannot be read back from an empty boundary |
| `Permutation(dom, perm)` | field `perm`, accepted back as a `finset.Permutation` | |
| `Layer(*inside, normalise)` | hand-written `__replace__` | `normalise` is an instruction, not state |
| `closed.Exp`, `python.finset.Permutation`, `kleisli.Monad` | not converted | not subclasses of `cat.Box`; nothing rebuilds them generically |

### What did not convert

`utils.replace` raises on these, rather than guessing:

- the term language: `Abstraction`, `Application`, `Let`, `Projection`,
  `Tuple`, `Variable` and `Constant` in `closed`, `biclosed` and
  `grammar.abstract`, and `FA`, `BA`, `FTR` and `BTR` in
  `grammar.categorial`. Terms have their own identity (alpha-equivalence,
  free variables). Their constructors take sub-terms the box does not
  store under those names.
- the gates `Ket(*bitstring)`, `Bra`, `Digits(*digits, dim)`,
  `Measure(n_qubits, destructive, override_bits)` and
  `Encode(n_bits, ...)`: variadic or renamed parameters. Each one is a
  small change, but none of them carries symbols, so nothing needs
  `replace` on them today.
- step 4, i.e. functors, hypergraphs and maps: not worth it. None of them
  has the rebuild-on-subclass problem. Hypergraphs compare up to
  isomorphism and functors hold callables, so dataclass `eq` would be
  wrong for both.

**Replace probe.** A pytest plugin recorded one instance of every
subclass of `cat.Box` that the unit suite builds (236 classes) and
checked `replace(box) == box` for each:

| | round-trips | raises | rebuilds a different box without raising |
|---|---|---|---|
| after step 1 | 159 | 71 | 5 (`Ket`, `Bra`, `Measure`, `Encode`, `Tuple`) |
| after step 3 | 196 | 34 | 5 |
| final | **207** | 28 | **0** |

The silent case is the dangerous one. `Measure(2, destructive=False)`
"replaced" itself as `Measure()`, because none of its parameters is a
field and all of them have defaults. `utils.replace` therefore refuses a
constructor that takes a parameter which is not a field. The 28 that
raise are the classes above, plus two probe artifacts: the drawing's
relabelled permutation (see below) and a jax tracer.

## Answers to the eight questions

1. **Inheritance.**
   - The whole tower can be frozen. `@frozen` on `cat.Arrow` freezes
     the fields of every subclass. Decorating a class freezes its exact
     instances against every assignment, so all the constructors of its
     ancestors must use `setattrs`.
   - Generated subclasses stay undecorated in source and work:
     `NamedGeneric` subscripts, `@factory`, and the `Feedback`, `Trace`,
     `Head`, `Tail` and `FollowedBy` that `feedback.generators` builds
     with `type()` all go through `__init_subclass__`. A frozen
     dataclass inheriting a non-frozen one, or the reverse, never came
     up: the existing frozen dataclasses (`Colour`, `Ribbon`,
     `categorial.BinaryTerm`) stay frozen.
   - Fields are ordered along the MRO, so `Box`'s `(name, dom, cod)`
     comes after `Arrow`'s `(inside, dom, cod)`. A generated `__init__`
     can never take `Box('f', x, y)`, which is why the arrow tower has
     hand-written constructors and an explicit `__match_args__` wherever
     the order differs.
   - **Gotcha:** a decorated subclass gets dataclass's own `__replace__`,
     overriding a hand-written one it inherits. That is why the `Sum` of
     every level stays undecorated.
   - **Gotcha:** `dataclass` turns a field's default into a class
     attribute. A default on a field that a base serves through a
     property (`zx.Spider.phase = 0`) shadowed the property, so every
     phase read as 0. And `hasattr(Rx, "data")` became true, which broke
     unpickling old circuits.
2. **The cyclic `Box`.**
   - `inside` is a derived field (`init=False, compare=False`), set by
     `object.__setattr__` in `__init__`: to `(self,)` in `cat` and to
     `(Layer(self),)` in `monoidal`.
   - Equality and hash go through `setoid`, which leaves `inside` out,
     so they never recurse into the cycle. A property would also work,
     but `Diagram.__init__` already writes `inside`, so a field keeps
     one code path.
3. **Equality and hash.**
   - Dataclass `eq` cannot replace `setoid` for arrows. A generator
     arrow equals its box (`f == f >> Id(f.cod)`) and a singleton sum
     equals its term, while dataclass `eq` requires the same class. So
     the arrow tower keeps `eq=False`.
   - `setoid` *is* derived from the fields now: the type, then every
     compared field. Subclasses no longer extend it by hand: `rigid`
     added `z`, `markov` its flags, `feedback` `time_step` and `gates`
     a `time_step` again, and all of those overrides are gone.
     `tensor.Box.setoid` listed its fields by hand and now reads them.
   - Classes that keep their own comparison: `Ty`, `Wire`, `Nat` and
     `Dim` (types), `Layer` (its components), `Sum` (a singleton is its
     term), `Bubble` (ignores `data` and `is_dagger`, see below),
     `QuantumGate` (by `repr`), and everything outside `cat`
     (hypergraphs up to isomorphism, `Equation`, functors).
   - `cat.Ob` uses dataclass `eq`, which is exact on the class where it
     used `isinstance`. No test noticed: every subclass with state
     defines its own.
4. **Transparency.**
   - `repr=False` everywhere in the arrow tower and on `cat.Ob`. The
     dataclass `repr` would print defaults, `inside`, every drawing
     option and class names without `factory_name`, and would lose the
     `.dagger()` suffix.
   - `eval(repr(x)) == x` holds as before: the transparency cells of the
     property matrix pass.
5. **Coercion and defaults.**
   - Constructors cast:
     - `Arrow` casts `dom` and `cod` to its `ob`;
     - `Ty` casts names to `Wire`;
     - `Permutation` casts lists to `finset.Permutation` and `Cofunction`
       to `op.Comarkov`;
     - `Spider` and `Swap` compute `name`, `dom` and `cod`, and `Layer`
       normalises.
   - `__post_init__` only works with a generated `__init__`, i.e. only
     on `cat.Ob`. Elsewhere the casts stay in the hand-written
     `__init__`.
   - `replace` keeps working where the constructor accepts back what its
     field holds. That took two small fixes: `Cofunction` now accepts an
     `op.Comarkov`, and `Swap` got a `__new__` that takes keywords.
   - No positional call in the tests or docs changed. What changed is
     styling by assignment, `box.color = "red"`, on classes whose
     instances are frozen. Those became constructor keywords: one test,
     the `spiral` helper and one notebook.
6. **`cached_property`.**
   - It works: it writes to `__dict__` directly. `Box.free_symbols` and
     `Layer.name`, `dom` and `cod` are cached on frozen instances.
   - What breaks is invalidation. `delattr(self, key)` raises on a frozen
     instance, so `Layer.__setstate__` uses `vars(self).pop(key)`.
   - No `__slots__` were added.
7. **Serialisation.**
   - Pickling and deep copying work unchanged: the state is restored
     into `__dict__`, bypassing `__setattr__`.
   - The legacy-state upgrades had to change, from "assign the old
     attribute, then update with the state" to merging dicts. That
     reversed precedence silently in two places, which the old pickles
     of the fixtures caught: `Arrow._boxes` against `inside`, and
     `Box._data` against `data`.
   - `from_tree` of a base class that decorates its subclass's result
     (`markov` flags, `rigid` `z`, `feedback` `time_step`) cannot use
     `replace`, because the subclass's constructor may not take those
     fields. Decoding is construction, so it uses `setattrs`.
   - Could `to_tree` be derived? A probe built a tree from the
     constructor fields: 172 of the 217 classes that `replace` covers
     round-trip through it. The rest hold values with no tree:
     `finset.Permutation`, `finset.Function`, `op.Comarkov`, complex and
     array data, callables. So a derived `to_tree` needs one encoder per
     *value type*, not per box class, and would change the tree format.
     It is not implemented.
8. **Cost.** See below.

## Bugs and oddities found on the way

1. `Drawing.bubble` sets `always_draw_label` on a temporary slice
   `left[0]` of a type, so the flag never reaches the drawing: on `main`,
   no node of a named bubble's drawing carries it. Freezing `Ty` made the
   write raise. The branch drops it, so drawings are unchanged. Upstream
   should decide whether it meant `left.inside[0]`.
2. `cat.Bubble.setoid` ignores `data` and `is_dagger`, so
   `f.bubble(data=1) == f.bubble(data=2)` holds on `main`. The branch
   keeps it, because `test_Bubble_dagger` needs
   `f.bubble().dagger() == f.dagger().bubble()` while
   `test_Bubble_data` needs the dagger to flip `is_dagger`. The two
   tests only agree because `is_dagger` is not compared.
3. On `main`, `Box('f', x, y, data=psi).subs((phi, 1), (psi, 2))`
   returns the box unchanged: `cat.Box.subs` reads its variables as
   `{(phi, 1)}`. The branch fixes it, since the generic `subs` needs the
   right variables. The list form `subs([(phi, 1), (psi, 2)])`, which the
   docstring of `Arrow.subs` advertises, raises a `SyntaxError` from
   `sympy.lambdify` in `utils.rsubs`, on `main` and on the branch alike.
4. `Drawing.permutation_box` builds a symmetric permutation and then
   overwrites its `dom` and `cod` with drawing types. The result does
   not round-trip through `replace` or its own constructor.
5. Four rebuild schemes coexisted, each covering a different subset of
   classes (see the summary).

## Regression tests

The eight cases of the prompt, one test per module:

- `test/monoidal.py::test_Bubble_subs_and_dagger_keep_the_drawing_options`
- `test/tensor.py::test_Bubble_dagger_keeps_its_func`
- `test/symmetric.py::test_Trace_subs`
- `test/feedback.py::test_Feedback_subs`
- `test/closed.py::test_Curry_subs`
- `test/rigid.py::test_Box_subs_keeps_z`
- `test/quantum/zx.py::test_Spider_lambdify`

There is also `test/utils.py::test_every_class_has_the_fields_of_all_its_bases`
for the diamond invariant. On `main` the eight cases fail exactly as the
prompt lists them:

```
FAIL bubble.subs keeps options
FAIL bubble.dagger keeps options
ERR  tensor.Bubble.dagger TypeError Box.__new__() got multiple values for argument 'name'
ERR  Trace.subs TypeError Trace.__init__() got an unexpected keyword argument 'name'
ERR  Feedback.subs TypeError Feedback.__init__() got an unexpected keyword argument 'name'
ERR  Curry.subs TypeError Curry.__init__() got an unexpected keyword argument 'dom'
FAIL rigid.Box.subs keeps z
ERR  zx.Z.lambdify TypeError Spider.__init__() got an unexpected keyword argument 'is_dagger'
```

and on the branch:

```
OK   bubble.subs keeps options
OK   bubble.dagger keeps options
OK   tensor.Bubble.dagger
OK   Trace.subs
OK   Feedback.subs
OK   Curry.subs
OK   rigid.Box.subs keeps z
OK   zx.Z.lambdify
```

## Checks

Run on the branch (`3cb54bd0`) and on `main` (`723e7690`) with the
same commands. `ty` is not configured on the base, so it was not run.

| Check | `main` | branch |
|---|---|---|
| `uv run pflake8 discopy` | clean | clean |
| `uv run pylint discopy` (`fail-under=9.05`) | 9.16 | **9.08**, passes, but below `main` |
| `uv run pytest --skip-extra -n auto` | 2058 passed, 82 skipped | 2073 passed, 83 skipped |
| `HYPOTHESIS_PROFILE=pr uv run pytest proptest/ -n auto -p no:benchmark --hypothesis-seed=0` | 188 passed, 26 skipped | 188 passed, 26 skipped |

The failing set is empty on both sides, so there is nothing to diff. The
extra test cases on the branch are the eight new tests and seven new
doctests. The extra skip is the new `Box.symbolic_fields` doctest, which
needs sympy (`+EXTRA`).

Pylint lost 0.08 for three reasons:
- it does not recognise `@frozen` as a dataclass decorator, hence 7
  `invalid-field-call` and one `invalid-match-args-definition`;
- it cannot see attributes set through `setattrs`, hence `no-member` up
  from 59 to 82, mostly `Ty.inside`;
- the overrides that only call `super()` now trip
  `useless-parent-delegation` (+3).

A slice proposed upstream would have to write `@dataclass(frozen=True,
init=False, eq=False, repr=False)` in full at each site, or ship a pylint
plugin, to keep the score from going down.

## Cost

Measured with `benchmark/` and `report.py --base`, `main` and the branch
run back to back on the same machine:

- 2 rounds at the default sizes;
- 1 round of the full tail (`BENCH_FLAGS=bench:full`) before the inline
  fix, and 1 after it;
- 1 base-against-base round, to measure the noise.

| Comparison | measurements | geometric mean | worst | above 25% |
|---|---|---|---|---|
| `main` against `main` (noise) | 123 | -0.4% | +5.9% | 0 |
| branch, default sizes, rounds 1 and 2 | 123 | +8.7%, +11.0% | +30.0% | 3 |
| branch, full tail | 173 | +8.4% | +46.2% | 7, all "Diagram k-fold series" |
| **branch, full tail, fields set inline in `Arrow` and `Box`** | 173 | **+7.1%** | **+22.0%** | **0** |

Before the fix, `report.py` flagged these regressions above 25%:

| suite | family | case | n | base (s) | head (s) | change |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| composition | Diagram | k-fold series | 200 | 1.3e-05 | 1.9e-05 | +46.2% |
| composition | Diagram | k-fold series | 100 | 1.2e-05 | 1.7e-05 | +41.7% |
| composition | Diagram | k-fold series | 50 | 1e-05 | 1.4e-05 | +40.0% |
| composition | Diagram | k-fold series | 500 | 2.1e-05 | 2.9e-05 | +38.1% |
| composition | Diagram | k-fold series | 1000 | 2.3e-05 | 3.1e-05 | +34.8% |

After it, `report.py` reports **PASS: no important regressions**. The
worst families are now transposition and conversion to hypergraphs, at
12–16%.

Where the time goes, per call (`timeit`, best of 5):

| | `main` | branch with `setattrs` | branch, inline |
|---|---|---|---|
| `d >> d` | 1.28 µs | 1.62 µs | 1.43 µs |
| `Box('g', x, x)` | 8.31 µs | 10.99 µs | 9.60 µs |
| `Layer(x, f, x)` | 2.61 µs | 2.86 µs | 2.83 µs |
| `x @ x` | 2.10 µs | 2.45 µs | 2.21 µs |

The cost is the frozen `__init__` going through `object.__setattr__`,
plus `setattrs` building a kwargs dict. A non-frozen dataclass would pay
neither. The unit suite, warm and back to back with
`MPLBACKEND=Agg`, takes 30.2s against 27.9s on `main` (+8%, with 15 more
tests). `finset.Permutation` was not touched: it is
already a plain dataclass and not a subclass of `cat`.

## Recommendation

**Propose the fields upstream; do not propose frozen, at least not yet.**

What is worth having is the declaration of what a box is built from:
- `replace` rebuilds any box correctly, which fixes the eight bugs and
  the class of bugs they belong to;
- `subs`, `lambdify`, `dagger`, `delay` and `setoid` are written once;
- four ad hoc rebuild schemes disappear;
- a probe can check `replace(box) == box` on every class. That would be
  a natural `Axiom` for the property matrix.

Freezing adds none of that. It costs:
- 64 `setattrs` call sites;
- a drawing layer that can no longer style boxes by assignment, with
  instances that are frozen or not depending on whether their exact class
  is decorated;
- pylint's view of every field set that way;
- most of the 7% slowdown.

It becomes cheap once the drawing builds its boxes from keywords rather
than mutating them, which is worth doing anyway. So propose it last.

Slices, each cut from upstream `main` and each small enough to read:

1. **Fields and `replace` in `cat`** (~250 lines of code and tests):
   - `utils.replace`, `inherit_fields` and the fieldless-parameter guard;
   - `cat.Arrow`, `Box`, `Sum` and `Bubble` as dataclasses
     *without* `frozen`, i.e. `dataclass(init=False, eq=False,
     repr=False)`, so no `setattrs`;
   - generic `subs`, `lambdify` and `dagger`;
   - the `subs((phi, 1), (psi, 2))` fix and the field test of `test/utils.py`.

   This alone fixes the bubble cases and `rigid.Box.subs` (once `z`
   is declared).
2. **The level fields** (~250 lines):
   - `time_step` (deletes `_args`/`_params`);
   - `deterministic` and `affine` (deletes `flagged`);
   - `z`, `is_mixed` and the rotation `phase`;
   - the hand-copied `rotate` and `dagger` replaced;
   - `setoid` derived from the fields;
   - the regression tests for `Trace`, `Feedback`, `Curry`,
     `tensor.Bubble` and `zx.Spider`, with their fields.
3. **The structural boxes and `delay` from fields** (~150 lines):
   - `left`/`right`, `perm`, the copy/merge views, spiders, cospans
     and the dual-rail boxes;
   - `Swap.__new__`;
   - `feedback.Box.delay` without `__getnewargs__`.
4. **Later, frozen**, after a separate change makes the drawing build
   boxes from keywords.

Not proposed as part of this: dataclass `eq` for arrows, which is wrong
for a generator against its box; a derived `to_tree`, which changes the
format; and the term language. To report as issues: the dead
`always_draw_label` write, `Bubble` equality ignoring `data`, and the
`subs` forms of bug 3.
