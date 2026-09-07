# TODO

> implement 1, 2 and 3
>
> (the potential solutions to the three architectural problems classified in
> the ty typechecking report:
> 1. Factory-pattern covariance: parameterise the ABCs over their diagram
>    type — Self-typed returns plus generic bounds — so the narrowing down
>    the tower is expressed as generics rather than overrides, and
>    re-enable `invalid-method-override` and `invalid-return-type`.
> 2. NamedGeneric runtime parameterisation: reimplement `NamedGeneric` on
>    PEP 695 generics with a `__class_getitem__` that typecheckers
>    understand, removing the `inconsistent-mro` ignores and the Unknown
>    cascades behind `unsupported-operator` and `unresolved-attribute`.
> 3. Unbounded object and arrow type variables in `abc`: give the type
>    variables Protocol upper bounds — Sized, Sequence, a duality protocol
>    for `.l`/`.r` — and re-enable `invalid-argument-type`,
>    `invalid-type-form`, `invalid-type-arguments`.)

- [x] Reimplement `NamedGeneric` on PEP 695 type parameters, port every
      subscripting class (`tensor`, `hypergraph`, `cmap`, `stream`, `para`,
      `interaction`, `hopf`, `quantum`) and drop the `inconsistent-mro`
      inline ignores
- [x] Give the `abc` type variables Protocol upper bounds and clean up the
      `ClassVar[C0]` / dynamic `Generic` forms
- [x] Express the tower's covariant narrowing with `Self` and the bounded
      type variables instead of unsound overrides
- [x] Re-enable the seven ignored rules one by one, fixing or locally
      ignoring what surfaces, until `ty check` passes with the smallest
      possible rule ignore list
- [ ] `pflake8`, full pytest, CHANGELOG entry, report
