> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Review round 1, cubic on `0f13368d`:

> P2: The functor in this test is ill-typed: `g: z -> z` is mapped to `Swap(z, y)`, which goes `z @ y -> y @ z`, but `z` maps to `z @ y`. The expected permutation is built from that wrong codomain, so the test does not check a valid functor. Use an endomorphism of `z @ y` (or a well-typed image for `g`) so the expected value comes from a real functor.

https://github.com/rel-int/discopy-next/pull/303#discussion_r4353227755

> P3: `@unbiased` still folds pairwise: `Channel.tensor(*others)` calls the binary `tensor` once per extra operand, so each step nests another `inside` closure and monad wrapper. For Channel codomains the functor path is therefore not a single n-ary combination, and the optimization described in the PR does not happen here. If the n-ary combination is the goal, `tensor` needs a genuinely variadic implementation that builds one `inside` over all summands.

https://github.com/rel-int/discopy-next/pull/303#discussion_r4353227769

- [ ] P2: `test_Functor_maps_a_layer_of_permutations_as_the_fold` uses a well-typed functor (`f` was ill-typed too), still failing on the prototype
- [ ] P3: no speed-up is claimed for `additive.Channel`, the decorator only stops the n-ary call raising: say so on the thread, make the CHANGELOG say it
