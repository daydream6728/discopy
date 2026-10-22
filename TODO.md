# TODO

> Implement markov and frobenius plumbing https://github.com/discopy/discopy/issues/472

Answers given live in the same session:

> Should the existing structural boxes become special cases of the new plumbing, the way Swap is a Permutation (#594)? "Yes, all plumbing (Recommended)": markov: Copy, Discard, Permutation and Swap are Functions, and Function(x, [0, 0]) returns Copy(x). frobenius: Cup, Cap, Permutation, Swap and phase-free spiders are Cospans. Every layer then truly alternates, and foliation fuses copies with swaps. Phased spiders (zx, tensor) stay generators.
>
> How should it be sliced into pull requests on discopy-next? "Two, stacked (Recommended)": first markov (plus comarkov) Function and Layer, then frobenius Cospan and Layer stacked on it.

This pull request is the second of the two, stacked on #243: frobenius.

## Mathematics

- The free hypergraph category on one object, i.e. the PROP of special commutative Frobenius algebras, is cospans of finite sets `dom -> apex <- cod` up to isomorphism of the apex (Lack 2004), composed by pushout and tensored by disjoint union. A point of the apex is a spider, its legs the elements of `dom` and `cod` sent to it; a point that no leg reaches is a scalar, the spider with no leg.
- A `frobenius.Cospan(apex, left, right)` holds a `finset.Cospan` and the type of each point: `dom[i] == apex[left[i]]` and `cod[j] == apex[right[j]]`. Every cospan is the cofunction `left` into its apex then the function `right` out of it: merges then copies.
- A `frobenius.Layer` is a tensor of generators and cospans. Permutations, swaps, phase-free spiders and the cups and caps of a self-dual wire are cospans; phased spiders are generators.
- The subclasses of `frobenius.Diagram` (`tensor`, `grammar.pregroup`, `quantum.zx`, `quantum.circuit`, `hopf`) keep their spiders as generators until they have a native cospan factory.

## Points

- [ ] `finset.Cospan`: pushout, disjoint union, swaps, spiders, cups, caps, trace; a `HypergraphCategory` in the property matrix
- [ ] `abc.HypergraphCategory.cospan` and `from_cospan`, a cospan in any hypergraph category
- [ ] `frobenius.Cospan`, with `Permutation`, `Swap`, `Cup`, `Cap` and phase-free `Spider` as cospans, and `Cospan(x, [0], [0, 0]) == Spider(1, 2, x)`
- [ ] `frobenius.Layer` alternates cospans and generators; foliation fuses them; `Diagram.spiders` of a type is one cospan
- [ ] functors, drawing, daggers, pickling, trees
- [ ] tests, docs, CHANGELOG
