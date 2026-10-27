# TODO

cubic's review of [#391](https://github.com/rel-int/discopy-next/pull/391), round 1:

> P2: `normalise()` can return a non-empirical model: equal row sums do not guarantee compatible marginals. Validate the normalized result with `assert_compatible()` before returning it, so signalling inputs fail instead of propagating an invalid model.

> P2: A zero-party diagram passes the new length check with `outputs == ()`, but this expression indexes `outputs[0]` and raises `IndexError`. Handle the empty output tuple or reject zero-party diagrams explicitly.

> P2: `sizes` is defaulted only when `measurements` is also omitted, so custom measurement families cannot use the documented optional `sizes` argument and default measurements ignore caller-provided sizes. Default `sizes` independently after resolving `measurements`.

> P3: The fraction is piecewise linear and not differentiable at its kinks; `Model.gradient` returns a subgradient there. The newline inside the code span also renders `Model. gradient`. Describe the subgradient and keep the identifier on one line.

- [WIP] @session_01XhK5oE7DUqFEBMsGrvpC1e-2026-10-27 09:36 `Model.normalise` checks its result is an empirical model
- [WIP] @session_01XhK5oE7DUqFEBMsGrvpC1e-2026-10-27 09:36 `Model.from_diagram` on a diagram with no party
- [WIP] @session_01XhK5oE7DUqFEBMsGrvpC1e-2026-10-27 09:36 `MessagePassingScenario` takes `sizes` with custom measurements and requires them
- [WIP] @session_01XhK5oE7DUqFEBMsGrvpC1e-2026-10-27 09:36 `CHANGELOG.md` says subgradient and keeps the identifier whole
