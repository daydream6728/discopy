# TODO

> can we use Hom at the use-sites as well? doesn't Annotated[object, ...]
> mean that the typechecker simply accepts any value?

- [x] `type Hom[C, A, B] = Annotated[C, A, B]`: the base substitutes, so
      `self: Hom[C2, A, B]` types as `C2` and the binder bound
      strengthens from the vacuous `object` to `C1` — verified green
      under ty with real law bodies; pyright expands the alias and
      rejects the generic bound, ty being the reference checker
- [x] One `unfold` shared by `bound_of` and `interpret`, the
      bare-variable sequent annotations of `discopy.abc` respelled with
      `Hom`, operator patterns and equation verdicts staying `Annotated`
- [x] `ty check` green, `pflake8`, pytest, CHANGELOG

> actually claude/proof-search-on-serde was an earlier experiment with
> type annotations for proof search, another more advanced branch at
> claude/diagram-search-strategies-766716 implements proper proof search
> based on pattern sequents. can you update this branch with the new
> setup? strive to unify as many concepts as possible into a single
> coherent, typeable implementation of property testing. ideally, only
> monoidal.Diagram should define a generic rule-based search strategy
> and all the other free categories should inherit it as is, only being
> extended with new rules.

- [x] Read `claude/diagram-search-strategies-766716` in full —
      `pattern.py`, `search.py`, `axioms.py`, the rule idiom of
      `monoidal` and each level — and map its concepts onto this
      branch's
- [x] Design the unification: their search semantics under our typed
      `Hom`/`Annotated` front-end, one generic rule-based strategy on
      `monoidal.Diagram`, levels only adding rules
- [x] Merge the branch (append-only), resolve, implement the unified
      design
- [ ] `ty check` green, `pflake8`, pytest, proptest fast profile,
      CHANGELOG
