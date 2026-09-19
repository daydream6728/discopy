# TODO

> can we use Hom at the use-sites as well? doesn't Annotated[object, ...]
> mean that the typechecker simply accepts any value?

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-19 20:20
      `type Hom[C, A, B] = Annotated[C, A, B]`: the base substitutes, so
      `self: Hom[C2, A, B]` types as `C2` and the binder bound
      strengthens from the vacuous `object` to `C1` — verify green under
      ty with real law bodies; pyright expands the alias and rejects the
      generic bound, ty being the reference checker
- [ ] One `unfold` shared by `bound_of` and `interpret`, the
      bare-variable sequent annotations of `discopy.abc` respelled with
      `Hom`, operator patterns and equation verdicts staying `Annotated`
- [ ] `ty check` green, `pflake8`, pytest, CHANGELOG
