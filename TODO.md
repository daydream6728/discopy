> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `symmetric`, bullets of #31:

- [ ] B72: whiskered `Swap` is a `Permutation` that functors cannot map: into `Matrix` (`KeyError`), `to_braided()` (`TypeError`), `Functor({Nat(1): x @ y})` (`Expected a permutation of length 6, got 3`); without changing what a functor sends a `Permutation` to when its codomain has `permutation` (B60, decision 3 of #56)
- [ ] B78, simplify part: `braided.Diagram.simplify()` dies on a foliated diagram; split into staircases first, as #219 did for `grad`
- [ ] B86: `Permutation(x @ y, iter([1, 0]))` is not a `Swap` and compares unequal to one
- [ ] B88: `symmetric.Layer.merge` refuses a pair that composes to the identity, so `foliation` leaves `p >> p[::-1] >> p` at three layers
- [ ] B88: `Layer.then` resolves to `cat.Arrow.then` and `Layer.ar is cat.Arrow`: is what is right said anywhere?
