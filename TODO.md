# TODO

USER, live 2026-10-19, verbatim:

> We have a Kleisli module already but we’re missing an Eilenberg Moore one: two cases, one for free algebras ie with M(A -> B) as morphisms A to B and one for arbitrary algebras. Let’s plan it first, we could go as far as a category of adjunctions for a monad with call by push value as the syntax

> ha yeah that was a mistake from my side, what you wrote makes sense and what i had in mind was not EM but the free algebra-enrichment over a monoidal category where arrows really are M(A -> B) not sure where that would fit? discopy.enriched could be a cool module

> 1. i don’t think adjunction as a sub module of eilenberg makes sense, maybe they can all be submodules of a monad module with discopy.monad.resolution instead of adjunction
> 2. Arrow is fine
> 3. start with Eilenberg
> 4. cbpv.Term would be awesome 🙌

The plan is #134; this pull request is its first slice, the two cases.

- [WIP] @session_01WREYbtVNgZQwbtqTkPP6wD-2026-10-19 15:40 `discopy.monad` package, `discopy.monad.free`: `Homomorphism[M]` between free algebras, `id` and `then` without the monad, `from_channel` and `to_channel` inverse to each other
- [ ] `discopy.monad.algebra`: `Algebra[M]` with `free`, its laws pointwise, `Homomorphism[M]` between algebras, the inclusion of free algebras
- [ ] examples: pointed sets for `Maybe`, `any` for `Powerset`, expectation for `Subdistribution`
- [ ] tests, API docs, `CHANGELOG.md`, `pflake8`, `pylint`, `pytest`
