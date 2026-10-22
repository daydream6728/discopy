> while you're waiting here's a stronger test case for your rewrites: implement all of Lafont's algebraic theory of Boolean circuits

(USER, live, 2026-10-22, attaching Lafont, *Towards an algebraic theory of Boolean circuits*, JPAA
184, 2003, on top of rel-int/discopy-next#224, double-pushout rewriting. Asked how: symmetric, τ
absorbed, i.e. his PROs read as symmetric monoidal categories so that the relations which are
axioms of those disappear; and every part, §2–§4, §3.3–§3.4, Appendix A and §4.2.)

Lafont presents monoidal categories of maps by generators and relations, and proves each
presentation complete by a rewrite system that takes every diagram to the canonical form of the map
it denotes. Over a symmetric hypergraph (Bonchi et al. II) the swap τ is wiring, so his rules that
only move τ hold on the nose, and each other rule is a double-pushout rule.

One premise of the plan was wrong and is corrected here: "commutativity cannot be oriented, so
normal forms are taken up to it". Up to commutativity alone is not enough, since associativity,
once oriented, still leaves `μ(a, μ(b, c))` and `μ(b, μ(a, c))` apart, and `x + x = 0` only fires
when both copies of `x` reach the same `μ`. So the (co)commutative (co)monoids are flattened: a
sum `μ_n : n -> 1` and a copy `δ_n : 1 -> n` of each arity, with `μ = μ_2`, `η = μ_0`, `δ = δ_2`
and `ε = δ_0`, and rules instantiated for each match, as for the ZX rules of #302. Normal forms are
then unique up to the order of the inputs of a sum and of the outputs of a copy, which a
hypergraph isomorphism that forgets those orders decides.

- [WIP] @session_01M8CWacKqbJVKPcDMd2m3AD-2026-10-22 21:00 `docs/notebooks/boolean-circuits.md`, part I, in this pull request:
  - [x] the encoding: τ absorbed, sums and copies flattened, rules as DPO steps of #224 built for
    each match, equality up to commutativity
  - [x] §2.3 𝔉, maps of finite sets (Theorem 3), and its surjections and injections
  - [x] §3 𝐋(ℤ₂), ℤ₂-linear maps (Theorem 5): the relations of Fig. 13 that are not symmetric
    monoidal axioms checked in the semantics, every diagram reduced to the canonical form of its
    matrix
  - [x] §3.3 𝐋(K) over GF(p), the relations of Fig. 36, with ℤ₂ as p = 2
  - [x] §2.1, §2.2 and §2.4 say why 𝔖, 𝔐 and 𝔄 are trivial or out of scope once τ is absorbed
- [ ] the later parts, filed as issues when this one is done:
  - §3.1–§3.2 𝐆𝐋(ℤ₂) and the κ presentations of 𝐋(ℤ₂) and its surjections (Theorems 6–8), 𝐆𝐋(K)
  - §3.4 the isometries 𝐎 and Euler angles (Theorem 9)
  - §4 𝔉[2], ℤ(ℤ₂), 𝔄(ℤ₂) and 𝐆𝐀(ℤ₂) (Theorems 10–11)
  - §4.2 Toffoli gates, F₃ from T₂ and T₃, the commutations, a check of Theorem 12
  - Appendix A: termination orders and critical peaks for DPO rewriting
- [x] `pflake8`, `pylint`, `pytest`, `docs/export_notebooks.py --check`
