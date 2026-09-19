# TODO

> i don't understand why we use A[X, Y] syntax in annotated but not
> directly as a signature (which is fine if it's what it takes to make
> the typechecker happy). it feels inconsistent and doesnt really make
> sense: the bounds of a morphism can only be assigned on quantified
> variables, e.g. for bifunctoriality i don't write Annotated[C2,
> (A @ C)[X, Z]], so why would i write Annotated[C2, C[Y, Z], D[Y, Z]] ?
> try to mimick as much as possible the exact typing that you'd see in a
> properly-, dependently-typed language.

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-19 18:40 The boundary
      of a higher cell is declared on its binder, not at its use-sites:
      `def tensor[X, Y, A: Annotated[object, C1, X, Y], ...]` mimicking
      the telescope `{A : C1 X Y}`, uses staying bare `Annotated[C2, A,
      B]` — the one bound form all of ty, pyright and mypy accept, since
      metadata is not part of the type; `bound_of` reads the level and
      boundaries off the lazily evaluated bound
- [ ] Respell the six TwoCategory declarations, drop the use-site
      `A[X, Y]` subscript from `Var.__getitem__` so there is one way
- [ ] `ty check` green, `pflake8`, pytest, CHANGELOG
