# TODO

> **6 issues found** across 18 files
>
> 1. `discopy/frobenius.py:209` P1: This override does not preserve flags for Frobenius subclasses that define their own rotation, so rotating a flagged spider, permutation, cup, or cap silently changes its cartesian semantics and equality. Wrap those specialized rotation results with `self.flagged(...)` as well.
> 2. `discopy/markov.py:257` P2: The new flags are lost by inherited `cat.Box.subs` and `cat.Box.lambdify`, which reconstruct `type(self)` with only `is_dagger` and `data`; a flagged box with symbolic data silently becomes total after either operation. Preserve both flags in those reconstruction calls.
> 3. `discopy/markov.py:289` P2: `flagged` does not copy true-valued flags, so a dagger or rotation can retain a target subclass's false default instead of inheriting this box's flags. Assign both flags from `self` unconditionally.
> 4. `discopy/markov.py:304` P1: Flag serialization does not round-trip subclasses that override `to_tree`: `frobenius.Spider.to_tree` omits these flags and `Spider.from_tree` reconstructs with the defaults. A serialized `Spider(..., is_affine=False)` therefore loads as affine and can become eligible for incorrect e-hypergraph rewrites.
> 5. `discopy/axioms.py:574` P2: The new documentation promises `params` for every `Self` term, but the `Self`-specific branch still calls `.strategy()` without them. Forward `**params` in that branch so weakened strategies constrain the generated term too.
> 6. `discopy/hypergraph.py:1339` P2: This check does not guarantee the `spider_factory` used below exists. A custom `MarkovCategory` can pass the guard and still fail with `AttributeError`; check the required factory capability or use the Markov API directly.

cubic's review of `2f5e229`, the round-3 head, verbatim. Each finding is a claim to reproduce before it is fixed.
Found while reading them: a spider's flags are its arity's, not a user's, and `markov.Merge(x, 0)`, the unit,
says it is deterministic, while the frobenius merge `Spider(2, 1, x)` says it is affine.

- [WIP] @session_01MY1Vs5CEhXgYwJcDnNwx6i-2026-10-18 03:05 Findings 1, 3 and 4, and the flags of a spider and a merge
- [WIP] @session_01MY1Vs5CEhXgYwJcDnNwx6i-2026-10-18 03:05 Finding 2, `subs` and `lambdify`
- [WIP] @session_01MY1Vs5CEhXgYwJcDnNwx6i-2026-10-18 03:05 Finding 5, the parameters of a testable shape of `Self`
- [WIP] @session_01MY1Vs5CEhXgYwJcDnNwx6i-2026-10-18 03:05 Finding 6, `make_bijective` over a Markov category with no spiders
