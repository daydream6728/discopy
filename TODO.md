> Let's finish the discopy-next bootstrap e.g. the wip from this PR should be merged in next and closed upstream https://github.com/discopy/discopy/pull/677/changes
> same for the ZX experiments: they become a single notebook in next
>
> this one is the last one that was opened by an agent under my human handle, let's merge whatever is still useful into next and close it https://github.com/discopy/discopy/pull/366

This branch is the discopy/discopy#366 part.

- [ ] Port what is still useful of discopy/discopy#366: the token-passing evaluation of a right-monogamous hypergraph over `python.additive.Function`, as `Hypergraph.pass_token`, the dual of `Hypergraph.__call__`
- [ ] Leave out what next superseded: the old `CMap` of #338/#348 (rewritten by #532), the alpha-equivalence `==` on terms (`alpha_eq`, #767) and `python.lambda_token` (its routing is read off the term's map, as its scope note says; `kleisli.token` walks the term, #639)
- [ ] Tests, CHANGELOG, pflake8, pylint, pytest
