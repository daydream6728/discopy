# TODO

> i want to use hom everywhere

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-22 09:10 Check that
      `parse` reads compound boundaries out of a `Hom` specialisation
      as it does out of raw `Annotated`, fixing `interpret` if not
- [ ] Spell every hom annotation with `Hom`, in `abc.py` and the level
      modules, leaving raw `Annotated` only where it is not a hom (an
      object premise) or where a boundary is a value a typechecker
      refuses as an alias argument
- [ ] Update the docs and CHANGELOG stating the convention
- [ ] `ty check`, `ruff check`, pytest, proptest fast profile, close
