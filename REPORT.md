# Report: DisCoPy's data structures as dataclasses

Branch `experiment/frozen-dataclasses`, cut from rel-int/discopy-next `main`
at `723e7690`. All commits are local to that branch. Everything below was
run on one machine (macOS, Apple silicon, Python 3.14.5), with
`MPLBACKEND=Agg`.

The experiment ran in two stages:
1. **frozen** dataclasses, as the prompt asked, up to commit `3cb54bd0`;
2. the same fields **without `frozen`**, from `0791ed03` on. That is the
   branch as it stands.

The frozen stage is kept in the history and measured below, because it
answers what freezing costs.

## Summary

- **The hypothesis holds without `frozen`.** Once a box declares as
  fields the data it is built from, `replace` rebuilds it with the other
  fields kept. All eight broken cases pass, and so do the rebuilds the
  levels above carried by hand. `subs`, `lambdify`, `dagger`, `delay` and
  `setoid` are written once, in `cat` or `feedback`, over the fields. The
  four ad hoc rebuild schemes go away:
  - `type(self)(name, dom, cod, ...)` in `cat`;
  - feedback's recorded constructor call (`_args`, `_params`);
  - markov's `flagged`, which mutated a rebuilt box to copy its flags;
  - `__getnewargs__` read by `delay`.
- **Plain `@dataclass` needs two additions to fit the hierarchy.** Both
  are in `utils`, about 100 lines:
  1. *Diamonds lose fields.* `dataclass` reads each base's fields with
     `getattr`, so a class that is not decorated inherits only the fields
     of the first decorated base in its MRO. 107 classes dropped fields
     that way, e.g. `pivotal.Box` lost `time_step` and every `zx` box lost
     `z`. `inherit_fields` runs from `__init_subclass__` of `cat.Ob` and
     `cat.Arrow`. It merges the fields of all bases, taking each one from
     the nearest base that has it.
  2. *Fields added by one level leak into every structural class below
     it.* `time_step`, `z`, `deterministic`, `affine` and `is_mixed` reach
     `Swap`, `Spider`, `Feedback` and the rest, whose constructors do not
     take them. `utils.replace` therefore gives back the
     `constructor_fields` of a class: those its `__init__` has a parameter
     for, or the ones not marked `derived()` when it takes `**kwargs`. It
     refuses a constructor that takes a parameter which is not a field,
     rather than letting it fall back to a default.
- **Without `frozen` it costs nothing measurable:**
  - benchmarks: +2.0% and −4.7% (geometric mean) over two full rounds,
    against +6.3% between two runs of `main`;
  - per call, composition and construction are within 1% of `main`;
  - pylint goes up, from 9.16 to 9.17.

  **With `frozen`** it cost:
  - 64 `object.__setattr__` call sites;
  - a drawing layer and user code that could no longer style a box by
    assignment, on some classes but not others;
  - 7% on the benchmarks;
  - pylint down to 9.08.

  Freezing bought nothing the fields do not already give.
- **Recommendation:** propose the fields upstream, in three slices, and
  leave `frozen` out. See the last section.

## What converted

Classes that declare fields are decorated with
`@dataclass(init=False, eq=False, repr=False)`: there are 33 such sites.
Their constructors, equality and representation stay hand-written.
Subclasses that add no field stay undecorated and get their bases' fields
from `inherit_fields`. A *derived* field (`utils.derived()`, i.e.
`init=False`) is one a constructor taking `**kwargs` computes rather than
takes. A *property-backed* field is declared but read through a property,
so its value is never stored twice.

| Class | Fields it is built from | How |
|---|---|---|
| `cat.Ob` | | a plain class as on `main`; `__init_subclass__` merges the fields of its subclasses, e.g. `Ty` |
| `cat.Arrow` | `inside, dom, cod` | hand-written `__init__` (`_scan` is an instruction) |
| `cat.Box` | `name, dom, cod, data, is_dagger` | `inside` derived and not compared (the cycle) |
| `cat.Sum` | `terms, dom, cod` | hand-written `__replace__` |
| `cat.Bubble` | `args, dom, cod, name, method` | `data` and `is_dagger` not compared, as before; cooperative `__init__`; takes `args=` |
| `monoidal.Ty` | `inside, dom, cod` | `name` derived, own `__eq__` |
| `monoidal.Layer` | `boxes_or_types` | hand-written `__replace__`: `normalise` is an instruction, so `replace` re-normalises |
| `monoidal.Bubble` | `+ drawing_name, draw_as_frame, draw_as_square, draw_vertically` | not compared |
| `feedback.Box` | `+ time_step` | replaces `_args` and `_params` |
| `feedback.Feedback`, `Trace` | `arg, dom, cod, mem, left` | `arg` property-backed (`Bubble.arg`) |
| `feedback.Head`, `Tail`, `FollowedBy` | `arg, time_step` (`+ is_dagger`) | |
| `markov.Box` | `+ deterministic, affine` | the constructor also takes `is_deterministic` and `is_affine`; `flagged` deleted |
| `rigid.Box` | `+ z` | `rotate` via `replace`, `dagger` inherited |
| `pivotal.Box` | join of `rigid.Box` and `feedback.Box` | hand-copied `rotate` and `dagger` replaced |
| `biclosed.Curry` | `arg, n, left` | `closed.Curry` spells out `(arg, n, left, time_step)` because `Timed` hides it behind `*args, **params` |
| `biclosed.Eval`, `Coeval` | `x, left` | same for the closed ones |
| `tensor.Bubble` | `+ func` | `*args` rather than `inside`, so `replace` can give `args` back |
| `tensor.Box.setoid` | | derived from the compared fields rather than listed by hand |
| `frobenius.Spider` | `n_legs_in, n_legs_out, typ, data` | stored; `name, dom, cod, deterministic, affine` derived because of `**params` |
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
| `grammar.categorial.BinaryTerm` and subclasses | `left, right` | were frozen dataclasses; now `eq=False`, compared through `setoid` |

### The prompt's list of constructors that do not store what they take

| Constructor | Decision | Why |
|---|---|---|
| `Swap(left, right)` | fields `left, right`; `name, dom, cod` not given back | the generating data is what the box is |
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
  free variables), and their constructors take sub-terms the box does not
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
subclass of `cat.Box` that the unit suite builds (236 classes) and checked
`replace(box) == box` for each:

| | round-trips | raises | rebuilds a different box without raising |
|---|---|---|---|
| after declaring the `cat` fields | 159 | 71 | 5 (`Ket`, `Bra`, `Measure`, `Encode`, `Tuple`) |
| after the structural boxes | 196 | 34 | 5 |
| final, frozen | 207 | 28 | 0 |
| **final, not frozen** | **210** | 26 | **0** |

The silent case is the dangerous one. `Measure(2, destructive=False)`
"replaced" itself as `Measure()`, because none of its parameters is a
field and all of them have defaults. Hence the guard in `replace`. The
26 that raise are the classes above, plus two probe artifacts: the
drawing's relabelled permutation and a jax tracer.

## Answers to the eight questions

1. **Inheritance.**
   - Every class from `cat` up is a dataclass, either decorated or
     through `inherit_fields`. Generated subclasses stay undecorated in
     source and work: `NamedGeneric` subscripts, `@factory`, and the
     `Feedback`, `Trace`, `Head`, `Tail` and `FollowedBy` that
     `feedback.generators` builds with `type()` all go through
     `__init_subclass__`.
   - With `frozen`, the whole tower could be frozen too. But a frozen
     dataclass cannot inherit from a non-frozen one, nor the reverse:
     dropping `frozen` forced the frozen `categorial` terms to unfreeze,
     and `cat.Ob` had to stay a plain class so that `Colour` and `Ribbon`
     can stay frozen.
   - Fields are ordered along the MRO, so `Box`'s `(name, dom, cod)` comes
     after `Arrow`'s `(inside, dom, cod)`. A generated `__init__` can
     never take `Box('f', x, y)`, so the arrow tower keeps hand-written
     constructors, with an explicit `__match_args__` wherever the order
     differs.
   - **Gotcha:** a decorated subclass gets dataclass's own `__replace__`,
     overriding a hand-written one it inherits. That is why the `Sum` of
     every level stays undecorated.
   - **Gotcha:** `dataclass` turns a field's default into a class
     attribute. A default on a field that a base serves through a property
     (`zx.Spider.phase = 0`) shadowed the property, so every phase read as
     0. And `hasattr(Rx, "data")` became true, which broke unpickling old
     circuits.
   - **Gotcha:** `copy.replace` and `dataclasses.replace` read each
     field's `init` flag, which describes the class that declared the
     field rather than the class being rebuilt. Use `utils.replace`.
2. **The cyclic `Box`.**
   - `inside` is a derived field (`init=False, compare=False`), assigned
     in `__init__`: to `(self,)` in `cat` and to `(Layer(self),)` in
     `monoidal`. When frozen, this went through `object.__setattr__`.
   - Equality and hash go through `setoid`, which leaves `inside` out, so
     they never recurse into the cycle.
3. **Equality and hash.**
   - Dataclass `eq` cannot replace `setoid` for arrows. A generator arrow
     equals its box (`f == f >> Id(f.cod)`) and a singleton sum equals its
     term, while dataclass `eq` requires the same class. So every arrow
     dataclass has `eq=False`. Without `frozen`, dataclass `eq` would also
     set `__hash__ = None`.
   - `setoid` *is* derived from the fields now: the type, then every
     compared field. Subclasses no longer extend it by hand: `rigid` added
     `z`, `markov` its flags, `feedback` `time_step` and `gates` a
     `time_step` again, and all of those overrides are gone.
     `tensor.Box.setoid` listed its fields by hand and now reads them.
   - Classes that keep their own comparison: `cat.Ob` and its types
     (`Ty`, `Wire`, `Nat`, `Dim`), `Layer` (its components), `Sum` (a
     singleton is its term), `Bubble` (ignores `data` and `is_dagger`, see
     below), `QuantumGate` (by `repr`), and everything outside `cat`
     (hypergraphs up to isomorphism, `Equation`, functors).
4. **Transparency.**
   - `repr=False` everywhere in the arrow tower. The dataclass `repr`
     would print defaults, `inside`, every drawing option and class names
     without `factory_name`, and would lose the `.dagger()` suffix.
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
   - `__post_init__` only works with a generated `__init__`, so the casts
     stay in the hand-written constructors.
   - `replace` keeps working where the constructor accepts back what its
     field holds. That took two small fixes: `Cofunction` now accepts an
     `op.Comarkov`, and `Swap` got a `__new__` that takes keywords.
   - No call in the tests or docs changed on the non-frozen branch,
     including styling by assignment such as `box.color = "red"`.
6. **`cached_property`.** It works either way, because it writes to
   `__dict__` directly. When frozen, invalidating it with `delattr` raised,
   so `Layer.__setstate__` had to use `vars(self).pop`. Without `frozen`,
   `main`'s code stands. No `__slots__` were added.
7. **Serialisation.**
   - Pickling and deep copying work unchanged.
   - The frozen stage had to rewrite the legacy-state upgrades as dict
     merges. That reversed precedence silently in two places, which the
     old pickles of the fixtures caught: `Arrow._boxes` against `inside`,
     and `Box._data` against `data`. The merges are kept, since they are
     correct either way.
   - Could `to_tree` be derived? A probe built a tree from the constructor
     fields: 172 of the 217 classes that `replace` covered round-trip
     through it. The rest hold values with no tree: `finset.Permutation`,
     `finset.Function`, `op.Comarkov`, complex and array data, callables.
     So a derived `to_tree` needs one encoder per *value type*, not per
     box class, and would change the tree format. It is not implemented.
8. **Cost.** See below.

## Bugs and oddities found on the way

1. `Drawing.bubble` sets `always_draw_label` on a temporary slice `left[0]`
   of a type, so the flag never reaches the drawing: on `main`, no node of
   a named bubble's drawing carries it. Freezing `Ty` made the write raise,
   which is how it surfaced. The branch keeps `main`'s line. Upstream
   should decide whether it meant `left.inside[0]`.
2. `cat.Bubble.setoid` ignores `data` and `is_dagger`, so
   `f.bubble(data=1) == f.bubble(data=2)` holds on `main`. The branch
   keeps it, because `test_Bubble_dagger` needs
   `f.bubble().dagger() == f.dagger().bubble()` while `test_Bubble_data`
   needs the dagger to flip `is_dagger`. The two tests only agree because
   `is_dagger` is not compared.
3. On `main`, `Box('f', x, y, data=psi).subs((phi, 1), (psi, 2))` returns
   the box unchanged: `cat.Box.subs` reads its variables as `{(phi, 1)}`.
   The branch fixes it, since the generic `subs` needs the right
   variables. The list form `subs([(phi, 1), (psi, 2)])`, which the
   docstring of `Arrow.subs` advertises, raises a `SyntaxError` from
   `sympy.lambdify` in `utils.rsubs`, on `main` and on the branch alike.
4. `Drawing.permutation_box` builds a symmetric permutation and then
   overwrites its `dom` and `cod` with drawing types. The result does not
   round-trip through `replace` or through its own constructor.

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

and on the branch, frozen or not:

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

`ty` is not configured on the base, so it was not run.

| Check | `main` (`723e7690`) | frozen (`3cb54bd0`) | not frozen (`e82fc457`) |
|---|---|---|---|
| `uv run pflake8 discopy` | clean | clean | clean |
| `uv run pylint discopy` | 9.16 | 9.08 | **9.17**, with `fail-under` raised to 9.17 |
| `uv run pytest --skip-extra -n auto` | 2058 passed, 82 skipped | 2073 passed, 83 skipped | 2071 passed, 83 skipped |
| `HYPOTHESIS_PROFILE=pr uv run pytest proptest/ -n auto -p no:benchmark --hypothesis-seed=0` | 188 passed, 26 skipped | 188 passed, 26 skipped | 188 passed, 26 skipped |

The failing set is empty everywhere, so there is nothing to diff. The extra
tests are the eight regression tests and the new doctests. The extra skip
is the `Box.symbolic_fields` doctest, which needs sympy (`+EXTRA`).

When frozen, pylint lost 0.08:
- it did not recognise the `@frozen` helper as a dataclass decorator;
- it could not see fields set through `object.__setattr__` (`no-member`
  up from 59 to 82).

Writing `@dataclass(...)` in full at each site and assigning fields
normally fixes both. The remaining new messages, e.g. three overrides
that only called `super()`, were cleared.

## Cost

`benchmark/` with `report.py --base`, `main` and the branch run back to
back on the same machine, full tail (`BENCH_FLAGS=bench:full`, 173
measurements):

| Comparison | geometric mean | worst | above 25% |
|---|---|---|---|
| `main` against `main`, two runs (noise) | +6.3% | +21.5% | 0 |
| frozen, fields via `setattrs` | +8.4% | +46.2% | 7, all "Diagram k-fold series" |
| frozen, hottest fields set inline | +7.1% | +22.0% | 0 |
| **not frozen, round 1** | **+2.0%** | +16.3% | **0** |
| **not frozen, round 2** | **−4.7%** | +20.8% | **0** |

`report.py` reports **PASS: no important regressions** for both
non-frozen rounds. Per call (`timeit`, best of 5):

| | `main` | frozen, `setattrs` | frozen, inline | not frozen |
|---|---|---|---|---|
| `d >> d` | 1.24–1.28 µs | 1.62 µs | 1.43 µs | 1.23 µs |
| `Box('g', x, x)` | 7.95–8.31 µs | 10.99 µs | 9.60 µs | 7.97 µs |
| `Layer(x, f, x)` | 2.55–2.61 µs | 2.86 µs | 2.83 µs | 2.52 µs |
| `x @ x` | 1.99–2.10 µs | 2.45 µs | 2.21 µs | 2.00 µs |

The whole cost of the frozen stage was `object.__setattr__` in the frozen
constructors. Declaring fields costs nothing per instance: `fields()`,
`constructor_fields` and `compared_fields` are read per class and
cached. The unit suite takes 29.1s against 29.0s on `main`, warm and back
to back.

## Recommendation

**Propose the fields upstream, without `frozen`.**

What is worth having is the declaration of what a box is built from:
- `replace` rebuilds any box correctly, which fixes the eight bugs and the
  class of bugs they belong to;
- `subs`, `lambdify`, `dagger`, `delay` and `setoid` are written once;
- four ad hoc rebuild schemes disappear;
- a probe can check `replace(box) == box` on every class. That would be a
  natural `Axiom` for the property matrix.

Freezing adds none of that, and costs:
- 64 `object.__setattr__` call sites;
- a drawing layer and user code that can no longer style boxes by
  assignment;
- 7% in time;
- pylint's view of every field set that way.

Slices, each cut from upstream `main` and each small enough to read:

1. **Fields and `replace` in `cat`** (~250 lines of code and tests):
   - `utils.replace`, `constructor_fields`, `inherit_fields` and the
     fieldless-parameter guard;
   - `cat.Arrow`, `Box`, `Sum` and `Bubble` as dataclasses, with generic
     `subs`, `lambdify` and `dagger`;
   - the `subs((phi, 1), (psi, 2))` fix and the field test of
     `test/utils.py`;
   - the two bubble regression tests.
2. **The level fields** (~250 lines):
   - `time_step` (deletes `_args`/`_params`);
   - `deterministic` and `affine` (deletes `flagged`);
   - `z`, `is_mixed` and the rotation `phase`;
   - the hand-copied `rotate` and `dagger` replaced;
   - `setoid` derived from the fields;
   - the regression tests for `rigid.Box`, `Trace`, `Feedback`, `Curry`,
     `tensor.Bubble` and `zx.Spider`, with their fields.
3. **The structural boxes and `delay` from fields** (~150 lines):
   - `left`/`right`, `perm`, the copy/merge views, spiders, cospans and the
     dual-rail boxes;
   - `Swap.__new__`;
   - `feedback.Box.delay` without `__getnewargs__`.

Not proposed: `frozen`; dataclass `eq` for arrows, which is wrong for a
generator against its box; a derived `to_tree`, which changes the format;
and the term language. To report as issues: the dead `always_draw_label`
write, `Bubble` equality ignoring `data`, and the list form of `subs` in
bug 3.
