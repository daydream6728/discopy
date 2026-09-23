# TODO

> what about dropping Hom, renaming HomType to Hom, and use
> Annotated[T, pat] everywhere
>
> yes, run it

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-23 09:00 In
      `pattern.py`: delete the `Hom` alias, rename `HomType` to `Hom`
      as an operand-generic front like `Unit`, read exactly one
      pattern from every `Annotated`, dropping the two-metadata and
      `TypeAliasType` branches of `interpret` and `sort_of`
- [ ] Respell the declarations of `abc.py` and `symmetric.py` as
      `Annotated[T, pat]`, follow the rename through `search.py`,
      `axioms.py` and the tests, asserting every sequent unchanged
- [ ] Docs and CHANGELOG
- [ ] `ty check`, `ruff check`, pytest, proptest fast profile, close
