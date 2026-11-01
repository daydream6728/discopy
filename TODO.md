# TODO

cubic's round on #427, verbatim:

> P2: `Spider.grad` is inherited by `zx.ZBox`, but `ZBox` encodes `phase` as a
> raw second amplitude rather than an angular phase. This difference formula
> therefore returns the wrong derivative for every symbolic `ZBox`; override
> or exclude `ZBox` from this phased-spider gradient, or change its
> representation to match the formula.

> P3: The changelog misattributes the old shifted-only formula to
> `quantum.zx.Spider.grad`; that implementation already used the difference
> formula. Attribute the spurious all-zero value to the old optyx
> implementation instead.

> P3: This changelog claim is incorrect for legless spiders: their sole scalar
> entry includes the phase-dependent amplitude, so its derivative is nonzero.
> Restrict the all-zero-entry explanation to positive-arity spiders.

The first is right and is the one that matters: `zx.ZBox(n, m, w)` truncates
to `zw.ZBox(n, m, [1, w])`, so its array is `P₀ + w·P₁` and its derivative is
`w′·P₁` — measured `1` on the all-one entry where the inherited formula gives
`−iπ/2`. It was wrong before this head too, `π·w′·ZBox(w + ½)` being nonzero
on the all-zero entry, so the override is a fix rather than a repair of the
head. The two others are wording.

- [x] `ZBox.grad` of its own, `w′` times `ZBox(n, m, 1) − ZBox(n, m, 0)`,
      which is `P₁`: measured to reproduce the difference quotient exactly at
      `(1, 1)`, `(1, 0)` and `(0, 0)`.
- [x] Add `ZBox` to the difference-quotient cells, so the three classes of
      this hierarchy are checked by the same oracle.
- [x] The changelog says *the old optyx implementation* rather than leaving
      "it" to be read as the sibling, and restricts the all-zero-entry
      reading to a spider with legs.
