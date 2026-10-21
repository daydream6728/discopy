> yes correct the misattributed quote: Daphne is wangdaphne, not daydream6728
> both improvements should go in this discopy PR

(toumix, 2026-10-21, interactive, on the review of [discopy/discopy#813](https://github.com/discopy/discopy/pull/813) by daydream6728:

> bias argument repeated on `run`, `fit` and `predict`, could be made an instance attribute to avoid duplication, so we'd specify it at instantiation.

by wangdaphne:

> Might make more sense to encode the values as `Rx(values/2)` (assuming they are between 0 and 1; otherwise it'll be hard to distinguish between values close to 0 and values close to 1 (`Rx(0) == Rx(1)`)

> Is it possible to implement the $\epsilon_i\tilde{\Delta}(\tilde{t})$?

and by toumix:

> Pasqal's qoolqit library provides a dimensionless parameterisation of their Hamiltonian: https://docs.pasqal.com/qoolqit/
> We should probably use that as a reference instead of the nanometers we're using now.)

- [WIP] @session_01KnHakJ3PdxvbpCKGgzGeJt-2026-10-21 15:40 `Reservoir.encode` rotates by half the value, so that a value in [0, 1] is one state
- [ ] `fit` returns a `Readout`, the affine map it fits, which `predict` applies: `bias` is said once, in `fit`
- [ ] `Rydberg` in qoolqit's dimensionless units, with its detuning map modulator εᵢ Δ(t)
- [ ] tests, CHANGELOG, then carry into discopy/discopy#813
