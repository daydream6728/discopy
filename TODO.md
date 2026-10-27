> can we express a boltzmann sampler as a discopy diagram with variables? then, using lambdify, we could extract a cvxpy convex optimization problem and tune it accordingly. following discopy-next#1, could we revise the property-testing setup using a rigorous boltzmann sampling fully self hosted in a discopy.boltzmann module, then every free diagram would have a class method to construct the boltzmann hypothesis search strategy itself as a diagram, which upon evaluation returns a hypothesis search strategy that samples free diagrams of this class.
> show me all such sampling diagrams when you're done

> no you don't need push access yet, just work locally (as if this was a claude code session, make a new branch off proptest/modular-search then we'll see if the experiment is fruitful if we wanna merge it)

— @joseph, in a session, 2026-10-27. Local experiment, cut from `proptest/modular-search` at `681c0a75`.

## Mathematics

The rules of a free category are a sequent calculus: a rule `ρ` with object
variables `X₁ … Xₖ`, premises `Hom[A_i, B_i]` and conclusion `Hom[A, B]`.
Fixing a finite set `U` of objects, the *universe*, every instance of `ρ`
whose premises and conclusion have their boundary in `U` is a production of a
context-free grammar, i.e. an operation of a multi-sorted operad:

- its sorts are the boundaries `Hom(A, B)` for `A, B ∈ U`, plus one sort `Hom`
  for an unknown boundary, with one production `Hom(A, B) → Hom` each;
- its productions are the instances of the rules, and one generator, a fresh
  box `A → B`, for each sort `Hom(A, B)`.

A derivation is a tree of productions, and the term it denotes is its image
under the algebra applying each rule.

*Revised once built:* indexing the sorts by coloured boundaries makes the
grammar explode (441 sorts and 14,670 productions for symmetric diagrams
`x → x` alone, a minute to tune, and one grammar per boundary asked for), so
the sorts are the *shapes* `m → n`, the numbers of wires, and a derivation
is typed from the root down by unification: each object variable is a fresh
object of placeholder wires, each conclusion is unified with its goal, the
wires no rule determines are drawn uniformly from a palette, and a
derivation that cannot meet its boundary is rejected. The terms are drawn
from the Boltzmann distribution of the shapes, coloured uniformly,
conditioned on being well-typed.

Every production `r` is a box with a
weight `w_r = z · u_ρ` as data, a monomial in `sympy` symbols: `z` marks the
size of a derivation, i.e. its number of nodes, `u_ρ` the applications of `ρ`.
The generating function of a sort `s` is the least solution of the system

    T_s = Σ_{r : … → s} w_r · Π_{p ∈ dom r} T_p,

and the Boltzmann distribution of the sort draws a derivation `t` with
probability `Π_{nodes} w_r / T_s`: the root by `w_r Π T_p / T_s`, then each
premise from its own sort, independently. It is uniform on the derivations of
a given size and boundary, which are not the diagrams up to the equations of
the category: a diagram is drawn once per derivation of it.

As diagrams, the equation of a sort is `T_s = Σ_r (T_{p₁} ⊗ … ⊗ T_{pₙ}) ⨾ r`,
a state `T_s` for each sort with its symbol as data: the *sampling diagram*.
Reading the data of each term as a product gives the system, see
`Specification.system`, and in log-space, `t_s = log T_s`, `θ = log z, log u`,

    minimise  t_root − ν · θ   subject to   t_s ≥ log Σ_r exp(θ · m_r + Σ_p t_p)

is convex and its optimum has expected marks `ν` (Bendkowski, Bodini, Dovgal,
2018): `sympy.lambdify` turns the right-hand sides into `cvxpy` expressions,
with `LogSumExp` printed as `cvxpy.log_sum_exp`.

## Points

- [x] TODO.md quoting the prompt, the design stated mathematically
- [x] `discopy.boltzmann`: `Production`, `Specification` with `system`, `tune` (cvxpy), `oracle` (fixpoint), `sample` (exact, iterative, with a size window) and `strategy` (hypothesis)
- [x] `Specification.diagrams` and `draw`: the sampling diagram of each sort, as an `Equation` of `monoidal` diagrams with `sympy` data
- [x] `FreeCategory.boltzmann(*, within, width)` compiles the rules of any free category into its `Specification`
- [x] `Arrow.strategy` and `symmetric.Diagram.strategy` draw from it rather than `search`, honouring the boundary they are asked for
- [x] doctests, `test/boltzmann.py` and the strategies tests: `pytest --skip-extra` passes 2237 here, 2186 on the base, neither failing
- [x] draw the sampling diagram of every free category to `docs/_static/boltzmann/`
- [x] lint: `pflake8`, `pylint`, `ruff`, `ty` on what this branch touches
- [x] admissible rules, as on #1 before `f5293a99`: a rule the others derive is checked but generates nothing, e.g. frobenius by spiders, swaps, cut and mix
- [x] the matrix under `pr` against the base `681c0a75`: the same 2872 cells, skips and expected failures, all passing but `frobenius.Diagram.str_transparency`, which the base breaks too on the term the new strategy draws: `Spider(1, 0, a) @ f` prints as one layer but reads back as `Cospan(a @ b, [0, 1], [1]) >> f`, to file as an issue
- [ ] open questions for the human: drop `search`? `sympy`/`cvxpy` as dependencies of `dev` (`uv.lock` not regenerated: no access to the PyTorch index here)? size by nodes or by boxes? feedback in frobenius, delayed or not? ~1000 lines, at the red line

## Comparison with the generators of #1

> compare the quality of the generated distributions of diagrams with the two from #1 and investigate whether we could make this boltzmann sampling the only way to generate diagrams for our property testing setup

— @joseph, in a session, 2026-10-27. `benchmark/generators/` reproduces it.

- [x] measure search, quotient and their mix on the base of #1, Boltzmann alone and mixed here: size, structure, diversity, speed, and the broken laws each finds
- [x] free Boltzmann draws mostly one node: tune near the singularity and condition on a window of sizes drawn by hypothesis
- [x] type derivations by unification rather than colour them top-down, so that a cut can meet a cup below it
- [x] tune generators to two fifths of the nodes, and drop the instances that vanish over an empty object
- [ ] drop `search`, which Boltzmann now subsumes
- [ ] a Boltzmann sampler of the wirings of a hypergraph category, boxes then wires, to replace `Hypergraph.strategy` and `CMap.strategy`, whose spiders of many legs, loops and compact cycles derivations rarely reach
- [ ] grammars that are not compiled from rules, for `TermBase`, the exponential types of `biclosed.Ty` and `ProofNet`
- [ ] `trace_left` and `curry_left` admissible in a symmetric category, conjugates of their right versions by swaps

## Wiring in normal form

> its not an issue if we double count, we are interested in generating good *enough* distributions, not in devising precise generating functions. for example, braids and traces can remain un-interpreted, most of what we want to quotient out is simple wiring equations such as snakes and swaps

— @joseph, in a session, 2026-10-27.

- [x] measure the wiring the equations erase: little, because derivations barely drew wiring at all, one swap in a hundred symmetric diagrams
- [x] draw wiring in blocks in normal form, `discopy.wiring`: permutations, Brauer and Temperley-Lieb diagrams, never composed with each other, braids, traces, feedback, spiders and curries left free
- [x] tune shares of generators, wiring and structure, which a tree of cuts and mixes bounds to half the nodes for the leaves
- [x] the matrix under `pr` passes every cell the base passes, in 26 minutes rather than 36; `pytest --skip-extra` passes 2253; 166 of the 176 broken laws found alone, 167 mixed with the quotient
