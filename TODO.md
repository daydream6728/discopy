# Experiment: DisCoPy's data structures as frozen dataclasses

## Goal

Find out whether DisCoPy's data structures (objects, types, arrows, boxes,
bubbles, layers, diagrams and the structural boxes) can be frozen
dataclasses, and what that costs. A frozen dataclass gives each class three
things in one declaration:
- `__match_args__`, so its instances are pattern-matchable;
- `__replace__`, so `copy.replace` works on Python 3.13+ and
  `dataclasses.replace` on 3.12;
- `__eq__`/`__hash__` over the fields it declares.

The hypothesis to test: `__replace__` is the right tool for rebuilding a box
"with these fields changed". Today, `subs`, `lambdify` and `dagger` do that
rebuild by hand in a base class, and it breaks on subclasses.

This is an experiment, not a pull request. The deliverable is a branch that
shows how far the conversion gets, plus a written report of what worked,
what broke and what it cost. Do not open pull requests on rel-int/discopy-next
or discopy/discopy.

## Where to work

- Repository: `daydream6728/discopy`. Work on a new branch
  `experiment/frozen-dataclasses`, cut from the current `main` of
  `rel-int/discopy-next` (fetch it as a second remote). Push only to that
  branch.
- Read first:
  - `AGENTS.md`, `RULES.md`, `STYLE.md` and `CONTRIBUTING.md` of
    rel-int/discopy-next. They say how the hierarchy is built and how to run
    the checks.
  - The two gotchas of README.md: a `Box` is a `Diagram` whose `inside` is
    `(Layer(box),)`, and the `@factory` decorator sets `C.ar = C`.
- Follow `RULES.md`: a `TODO.md` with this prompt copied verbatim at the top
  and the work as checkboxes. History is append-only.

## Why: what is broken today

`cat.Box.subs`, `lambdify` and `dagger` rebuild with
`type(self)(name, dom, cod, data=..., is_dagger=...)`. `cat.Bubble`'s
versions do the same with `type(self)(*args, dom=..., cod=..., name=...,
method=..., data=..., is_dagger=...)`. That is the base class's constructor,
used on every subclass. About 190 subclasses of `cat.Box` inherit these
methods while their constructors take something else, e.g.:
- `Swap(left, right)`, `Copy(x, n)`;
- `Spider(n_legs_in, n_legs_out, typ)`;
- `Trace(arg, left, dom, cod, mem)`, `Feedback(arg, dom, cod, mem, left)`,
  `Curry(arg, n, left)`;
- `rigid.Box(..., z)`, `tensor.Bubble(inside, func)`.

Most of them escape only because a box with no free symbols returns `self`
from `subs`/`lambdify`, and the structural boxes override `dagger`. Every
case below reproduces on rel-int/discopy-next `main` and should pass at the
end of the experiment. Make them regression tests:

```python
from sympy.abc import phi
from discopy import monoidal, symmetric, feedback, closed, rigid, tensor
from discopy.quantum import zx

x = monoidal.Ty('x')
bubble = monoidal.Box('f', x, x, data=phi).bubble(
    drawing_name="g", draw_as_square=True)
assert bubble.subs(phi, 1).drawing_name == "g"       # drops the options
assert bubble.dagger().draw_as_square                # drops the options

d = tensor.Dim(2)
tensor.Bubble(tensor.Box('t', d, d, [phi, 0, 0, 1]), func=abs).dagger()
# TypeError: Box.__new__() got multiple values for argument 'name'

y = symmetric.Ty('y')
symmetric.Box('f', y @ y, y @ y, data=phi).trace().subs(phi, 1)
# TypeError: Trace.__init__() got an unexpected keyword argument 'name'

X = feedback.Ty('x')
feedback.Box('g', X @ X.delay(), X @ X, data=phi).feedback().subs(phi, 1)
# TypeError: Feedback.__init__() got an unexpected keyword argument 'name'

c = closed.Ty('c')
closed.Box('h', c @ c, c, data=phi).curry().subs(phi, 1)
# TypeError: Curry.__init__() got an unexpected keyword argument 'dom'

assert rigid.Box('r', rigid.Ty('a'), rigid.Ty('b'), data=phi, z=1)\
    .subs(phi, 1).z == 1                              # silently resets to 0

zx.Z(1, 1, phi).lambdify(phi)(0.5)
# TypeError: Spider.__init__() got an unexpected keyword argument 'is_dagger'
```

The open pull request rel-int/discopy-next#1 works around the bubble cases
with an ad hoc `Bubble.keywords` property: each subclass lists its extra
constructor arguments. That fixes only the two bubble cases, and the
experiment should make it unnecessary. Do not port `keywords`.

## What a constructor stores today

A probe recorded, over the unit suite, whether each constructor parameter
given a value ends up as an attribute of the same name, which is the
dataclass convention. Most do, up to coercion (e.g. a `dom` given as a
string is stored as a `Ty`, which a dataclass would do in `__post_init__`).
The ones that do not are mostly structural boxes taking their generating
data:
- `Swap(left, right)`, `Copy(x, n)`, `Merge(x, n)`, `Spider(n_legs_in,
  n_legs_out, ...)`, `Permutation(dom, perm)`;
- `closed.Exp`, `python.finset.Permutation(size, inside)`, `kleisli.Monad`;
- `Layer`'s `normalise` flag, which is an instruction rather than state.

Each of these needs a decision: declare its generating data as fields and
derive `name`, `dom` and `cod` from them, or keep a hand-written
`__replace__`. Record which one you chose for each and why.

## Questions the experiment should answer

1. **Inheritance.** A frozen dataclass cannot inherit from a non-frozen one,
   or the other way round, and fields are ordered along the MRO.
   - Can the whole tower (`cat` → `monoidal` → `braided` → `symmetric` →
     ...) be frozen, with its diamond inheritance, e.g.
     `symmetric.Diagram(balanced.Diagram, SymmetricCategory)`?
   - Can the generated subclasses (`NamedGeneric` subscripts, `@factory`,
     the per-level `Box`/`Swap` classes) stay undecorated and still work?
2. **The cyclic `Box`.**
   - How does a frozen `Box` hold `inside = (Layer(self),)`?
     `object.__setattr__` in `__post_init__`, a property, or something else?
   - How do `__eq__`/`__hash__` avoid recursing through it?
3. **Equality and hash.** DisCoPy compares by `setoid()`.
   - Can dataclass `eq` replace it, field for field and type included?
   - Which classes must keep `eq=False` and their own comparison (e.g.
     hypergraphs up to isomorphism, `Equation`)?
4. **Transparency.** `eval(repr(x)) == x` must hold, and `repr` omits
   defaults and names classes by `factory_name`. Keep `repr=False` wherever
   the dataclass repr would differ, and say where.
5. **Coercion and defaults.**
   - Where does `__init__` cast its arguments, e.g. a name to an `Ob`, or a
     list to a `Ty`, or compute a default `dom`/`cod`?
   - Does `__post_init__` with `object.__setattr__` keep `replace(...)` and
     the existing call signatures working?
   - Are the positional calls of the tests and docs unchanged?
6. **`cached_property`.** Does it still work on the frozen classes? It writes
   to `__dict__` directly, so it should, unless you add `__slots__`.
7. **Serialisation.** Keep `to_tree`/`from_tree`, pickling and deep copying
   working. Are they simpler with fields declared, and could `to_tree` be
   derived from them?
8. **Cost.** Measure performance with the benchmarks of `benchmark/`.
   - Use `report.py --base`, comparing with `main` on the same machine.
   - Frozen `__init__` goes through `object.__setattr__`, and
     `finset.Permutation` and `Layer` are built millions of times by the
     unit suite.
   - Report regressions above 25%.

## Suggested order

Stop wherever the cost stops being worth it, and say so.

1. `cat.Ob`, `cat.Arrow`, `cat.Box`, `cat.Bubble`, `cat.Sum`. Then derive
   `subs`, `lambdify` and `dagger` from `replace` once, in `cat`, and delete
   the hand-written rebuilds the levels above carry.
2. `monoidal.Ty`, `Layer`, `Diagram`, `Box`, `Bubble`, then the other
   levels' boxes and bubbles: `rigid.Box` with `z`, `tensor.Bubble` with
   `func`, `Trace`, `Feedback` and `Curry`.
3. The structural boxes: `Swap`, `Cup`/`Cap`, `Copy`/`Merge`, `Spider`,
   `Permutation`.
4. Anything else worth it: functors, hypergraphs, maps.

## Checks

Run on every step and paste the output into the report:
- `uv run pflake8 discopy`
- `uv run pylint discopy`, at or above `fail-under`
- `uv run ty check`, if `ty` is configured on the base
- `uv run pytest --skip-extra -n auto`
- `HYPOTHESIS_PROFILE=pr uv run pytest proptest/ -n auto -p no:benchmark
  --hypothesis-seed=0`
- the benchmarks above, against `main`.

Diff the failing set against the same commands on the base, as
CONTRIBUTING.md explains: a sandbox can fail some tests for environment
reasons.

## Report

Write a `REPORT.md` at the root of the branch and delete `TODO.md` once
every box is done or filed. The report should contain:
- what converted, what did not, and why, class by class or level by level;
- the answers to the eight questions above;
- the regression tests above, now passing;
- the checks run, with their output;
- the benchmark comparison;
- a recommendation: whether to propose it upstream, and as which small
  slices.

---

- [ ] reproduce the eight broken cases on `main`
- [ ] baseline: checks and benchmarks on `main` (723e7690)
- [ ] step 1: `cat.Ob`, `Arrow`, `Box`, `Bubble`, `Sum`; `subs`/`lambdify`/`dagger` from `replace`
- [ ] step 2: `monoidal.Ty`, `Layer`, `Diagram`, `Box`, `Bubble`; `rigid.Box`, `tensor.Bubble`, `Trace`, `Feedback`, `Curry`
- [ ] step 3: structural boxes, `Swap`, `Cup`/`Cap`, `Copy`/`Merge`, `Spider`, `Permutation`
- [ ] step 4: functors, hypergraphs, maps, if worth it
- [ ] regression tests for the eight cases
- [ ] checks and benchmarks on the branch, diffed against the base
- [ ] `REPORT.md`
