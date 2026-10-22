> while you're waiting here's a stronger test case for your rewrites: implement all of Lafont's algebraic theory of Boolean circuits

(USER, live, 2026-10-22, attaching Lafont, *Towards an algebraic theory of Boolean circuits*, JPAA
184, 2003. Part I, maps and linear maps, is #310; the rest is #311, of which this is §4: the
Boolean functions 𝔉[2] and their subcategories ℤ(ℤ₂) and 𝔄(ℤ₂).)

The encoding is part I's: τ is wiring, and the commutative monoids are flattened, here the
conjunction ∧ too, with μ′ = ∧₂ and η′ = ∧₀. The canonical form of a Boolean function is its
algebraic normal form: copies of the inputs, then a conjunction for each monomial, then a sum for
each output. Cancelling two equal monomials is not a convex match when a third monomial shares one
of their variables, so the rules here take the convex hull of the boxes they are about.

- [x] §4 in `docs/notebooks/boolean-circuits.md`:
  - [x] the semantics, a functor into `python.Function` with each generator as its function on
    bits, and a rule as the convex hull of some boxes with its right side transformed
  - [x] Theorem 10: the relations of Fig. 40 that are not on τ checked in the semantics, every
    Boolean circuit reduced to its algebraic normal form
  - [x] ℤ(ℤ₂) and 𝔄(ℤ₂), the zero-preserving and the affine maps, by the generators they keep
- [x] `docs/export_notebooks.py --check`
