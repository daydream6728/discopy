# TODO

> i dont like the fact that type variables have to be imported, i really
> want to use def tensor[...](...) syntax, is there a clean way to do it?

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-19 17:10 Metavariables
      as PEP 695 type parameters: `annotated` evaluates each annotation
      in the scope of the function's own `__type_params__`, kinds read
      off plain class bounds, `def cups[X: Atom]`, operator patterns
      quoted, `Annotated[C1, "X @ X.r", ()]`, since ty types a bare
      operator on a type parameter as one on `TypeVar`
- [ ] Respell the declarations of `abc` and `test/axioms.py`, drop the
      module-level alphabet `A` to `Z` and its imports
- [ ] `ty check` green, `pflake8`, pytest, CHANGELOG
