> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Ruled live by USER (10-22) on B47 with B8, "spider pairing at frobenius":
https://github.com/rel-int/discopy-next/issues/31#issuecomment-6350437415

- [ ] B8: `Tensor.cup_factory` on compound dims returns `Tensor.cups`
- [ ] B47, compact and below: the `CMap` contraction pairs a bent wire's factors nested, one index per atomic factor, reversed on the adjoint end
- [ ] B47, frobenius: a cup or cap on a self-dual object is `Tensor.spiders`, flat, on both paths
- [ ] Regression tests per level (rigid, pivotal, compact, frobenius) and for B8
- [ ] `CHANGELOG.md`
