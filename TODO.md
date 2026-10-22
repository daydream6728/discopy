# TODO

> Implement markov and frobenius plumbing https://github.com/discopy/discopy/issues/472

Answers given live in the same session:

> Should the existing structural boxes become special cases of the new plumbing, the way Swap is a Permutation (#594)? "Yes, all plumbing (Recommended)"
>
> The comarkov split is already on next main (#102). Should comarkov get its own plumbing too, the dual of markov's? "Yess the dual but implement it via a discopy.op module as in this issue https://github.com/discopy/discopy/issues/646"
>
> How should it be sliced into pull requests on discopy-next? "Two, stacked (Recommended)"
>
> Which side should `op` wrap? "op.Comarkov[finset.Function] (Recommended)"
>
> frobenius.Diagram inherits both markov and comarkov, so the two plumbing classes need distinct factory names. What should they be called? "Function / Cofunction (Recommended)"

This pull request is the first of the two: markov and comarkov. The second, stacked on it, does frobenius.

## Mathematics

- A symmetric layer is a tensor of generators and permutations. Permutations form the free symmetric category on one object.
- The free Markov category on one object is `FinSet^op`. A `markov.Function(dom, f)` sends output `i` to input `f[i]`, i.e. `cod[i] == dom[f[i]]`. An input that no output reads is discarded, and one that several outputs read is copied. It holds a `finset.Function`, which already is `FinSet^op`: its list runs from `range(cod)` into `range(dom)`.
- The free comarkov category on one object is `FinSet`, i.e. `op.Comarkov[finset.Function]`. A `comarkov.Cofunction(cod, f)` sends input `i` to output `f[i]`, i.e. `dom[i] == cod[f[i]]`. It is the formal reverse of `markov.Function(cod, f)`, which is its dagger when the category is both.
- A `markov.Layer` is a tensor of generators and functions, and a `comarkov.Layer` is a tensor of generators and cofunctions. Adjacent plumbing tensors into one box, and two layers of plumbing alone compose into one.

## Points

- [x] `discopy.op`: `Category`, `Monoidal`, `Symmetric`, `Markov`, `Comarkov`, each wrapping an arrow `inside` of `category` with `dom == inside.cod`; testable from the underlying category's strategy
- [x] `finset.Function` is declared a `MarkovCategory`
- [ ] `markov.Function`, with `Copy`, `Discard`, `Permutation` and `Swap` as functions, and `Function(x, [0, 0]) == Copy(x)`
- [ ] `markov.Layer` alternates functions and generators; foliation fuses them
- [ ] `comarkov.Cofunction` holding an `op.Comarkov[finset.Function]`, with `Merge`, `Noise`, `Permutation` and `Swap` as cofunctions
- [ ] `comarkov.Layer`
- [ ] functors, drawing, daggers, pickling, trees
- [ ] `closed` and `neural.network` get their own functions and cofunctions
- [ ] tests, docs, CHANGELOG
