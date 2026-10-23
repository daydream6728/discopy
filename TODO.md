> while you're waiting here's a stronger test case for your rewrites: implement all of Lafont's algebraic theory of Boolean circuits

(USER, live, 2026-10-22, attaching Lafont, *Towards an algebraic theory of Boolean circuits*, JPAA
184, 2003. Part I, maps and linear maps, is #310; §4.1's Boolean functions are #316; the rest is
#311, of which this is §4.2: the Toffoli gates and Theorem 12.)

Theorem 12 is a generation theorem, not a presentation: every even permutation of ℤ₂ⁿ is a
circuit of τ, T₁, T₂ and T₃, and Lafont, after Musset, proves it with 3-cycles and no canonical
form. So the section makes the proof a construction, checked in the semantics, and the rewriting is
where the paper has equations: the involutions Tᵢ ∘ Tᵢ = id, the four commutations it draws, and
F₃ = T₂ T₃ T₂.

- [x] §4.2 in `docs/notebooks/boolean-circuits.md`:
  - [x] the gates T₁, T₂, T₃, Tₙ as boxes with their permutations, τ as wiring, and Lemma 14
  - [x] Theorem 12 as a construction: an even permutation as 3-cycles, each 3-cycle an affine
    conjugate of one standard 3-cycle, the standard one a commutator of Cᵏ NOT gates, each of those
    T₃s with one borrowed wire; checked on random even permutations for n = 4, 5
  - [x] n ≤ 3: every permutation of ℤ₂³ is a circuit of the four, odd ones too
  - [x] the equations of §4.2 as rules: involutions and the commutations, checked in the
    semantics, applied by double-pushout rewriting to shorten the constructed circuits
  - [x] the Fredkin gate F₃ = T₂ T₃ T₂
- [x] `docs/export_notebooks.py --check`
