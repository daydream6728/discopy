# TODO

> In `discopy/abc.py` at line 198:
> ```python
>             cls, f: Annotated[C1, ARROW]) -> Equation[C1]:
> ```
> should be unitality[A, B](cls, f: Annotated[C1, Hom(A, B)]) ->
> Equation[Annotated[C1, Hom(A, B)]]
>
> In `discopy/abc.py` at line 252:
> ```python
>             cls, f: Annotated[C1, ARROW]) -> Equation[C1]:
> ```
> should be dagger_involution(cls, f: Annotated[C1, Hom(A, B)]) ->
> Equation[Annotated[C1, Hom(A, B)]]
>
> here are a few comments, apply the same reasoning on all axioms and
> rules and eliminate the need of ARROW, OB and TERM altogether

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-29 Respell every
      `ARROW` premise as `Hom(A, B)` on fresh binders and every `OB`
      premise as `Ob(X)`, the `Equation` return carrying the hom type
      of its terms; drop the `OB`, `ARROW` and `TERM` constants, a
      `Self` premise mapping to its sort inline
- [ ] Validate: rules byte-identical, all axioms parse and draw, ruff,
      ty, pytest, fast + dev matrix, CHANGELOG, close
