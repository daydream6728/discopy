> open a draft PR with just the DSL part of #1, merge main into it and rebase this #90 on that

- [x] carve the sequent DSL of #1 (`063129c1`) onto `main`, without the search: the sorts, the formers, `Declaration`, `Axiom`, `inhabits`; `main`'s laws restated in it
- [x] merge `main` into it (cut from `main` at `463ed5b`)
- [ ] #90 on this branch: retarget its base here and merge this branch into it (a merge, not a rebase: `RULES.md` 4)
- [ ] #103, stacked on #90, follows once #90 has merged this branch
