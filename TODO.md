# TODO

> looks like we're mixing TypeVar with Var, and using type-level
> syntax like A and Tensor[A, A] to express patterns. sorry to bring
> this up again (possibly the third attempt): I'd like to investigate
> again the option of using operators to write patterns. the docs of
> typing.Annotated says any value is acceptable as an annotation, the
> issue we had was that operators weren't defined on typevars. could
> we make it work by making a clearer separation between type-level
> data and value-level patterns? the way i see it, instead of
> injecting C0 and C1 into the annotation, evaluation scope, they'd
> be pattern constructors just like Hom is currently. instead of
> directly using type variables like A, we have a lifting operation
> class Ob[C0: Category, C1: Category, T: Category[C0, C1]](
> Pattern[C0]) and write Ob(A: TypeVar), similarly instead of A @ B,
> we'd do Ob(A) @ Ob(B). here __matmul__ replaces Tensor[A, B],
> constructing a `class Tensor[T: MonoidalCategory](Pattern[T])`,
> similarly class Hom[T: Category](Pattern[T]) replaces Hom[A, B]
> with Hom(p1: Pattern[T], p2: Pattern[T]): Pattern[T], etc...
> in a new branch, completely reimplement the pattern language to be
> structured this way. remove all type-hacks while keeping ty check
> green. you are only allowed to get back to me when the size of this
> new branch is 1000LOC less than the current. in the worse case,
> sacrifice doctests and unit tests if you can't decide what to cut
> down from the actual logic.

Baseline on `claude/sequent-annotations` at `58af1dc4`: 42324 lines
of Python, 126963 lines tracked in total.

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-29 Reimplement
      `discopy.pattern` on value-level constructors: `Ob(A)` lifts a
      type parameter once, `@`, `.l`, `.r`, `<<`, `>>`, `**` and
      `Hom(p, q)` build the compound patterns, the subscript
      machinery goes — `interpret`, `sort_of`, `head_of`, `operand`,
      the `__class_getitem__` of every pattern class and the fronts
      `L`, `R`, `Over`, `Under`
- [ ] Respell every declaration, rule and axiom on the new spelling,
      the coarse type in `Annotated` for the typechecker and the
      pattern value beside it, no type-hacks left
- [ ] Cut what the LOC budget demands — machinery docs first,
      doctests and unit tests of deleted machinery next — until the
      branch is 1000 lines smaller than `claude/sequent-annotations`
- [ ] Validate: ruff, ty, pytest, fast + dev matrix, CHANGELOG,
      close
