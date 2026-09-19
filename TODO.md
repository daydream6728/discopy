# TODO

> rebase on latest discopy/discopy:main and solve the new type errors, ty check must pass

- [ ] Fetch `discopy/discopy:main` and merge it into this branch
      (RULES.md forbids rebasing a published branch, so merge)
- [ ] Resolve the merge conflicts
- [ ] Restore the fixes a stray checkout reverted before they were
      committed: the PERMUTATION_HAS_NO_OFFSET message, the Ty argument of
      biclosed Eval and Coeval, the Drawing argument of backend.draw, the
      diagram class of the recursive factories, the conventional Node keys,
      the parameter declarations of NamedGeneric, the dtype local of
      tensor setstate and the categorial term declarations
- [ ] Solve the type errors new code introduces until `ty check` passes
- [ ] `pflake8`, full pytest, CHANGELOG entry if needed, delete TODO.md, push
