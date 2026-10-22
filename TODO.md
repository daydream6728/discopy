> sounds about right, go ahead. proceed according to the following orders: create a new discopy-next PR #X that targets #214 (updating it with the new changes from #1, and other points made in the review above), then change the target of #1 to #X (splitting the sequent DSL from the PR).

— @daydream6728, in a session, 2026-10-22. #X is this branch, `proptest/sequents`, cut from the head of #214 (`19011ac2`); the DSL of #1 is read at `946b1f5`.

- [ ] `Equation[T]` is a generic class, as on #1, rather than a `NamedGeneric`: `substitute` and `inhabits` lose their special case
- [ ] `failing` and `inapplicable` are declared on `Declaration`, with `applicable`, as on #1
- [ ] `sliding` slides a morphism `k: N -> M`, as on #1, rather than an endomorphism of the memory
- [ ] the formers and sorts no law reads go: `Unit`, `Over`, `Under`, `Repeat` and `Count`
- [ ] `substitute` looks up variables only, rather than hashing every annotation and hiding the `TypeError`
- [ ] `position` is tested on every enrolled category: its scope reads `C0` and `C1` as `parameters` says
- [ ] `Former` says that its subscript is a type while open and an object once closed
- [ ] merge this branch into #1, the DSL resolved as here
- [ ] restore #214's `TODO.md` in place of this one, so that merging into #214 leaves its own
