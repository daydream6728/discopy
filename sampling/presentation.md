---
title: Sampling string diagrams
marimo-version: 0.23.16
layout_file: layouts/presentation.slides.json
---

```python {.marimo hide_code="true"}
import json
import statistics

import marimo as mo
import matplotlib.pyplot as plt
import numpy as np

RESULTS = mo.notebook_dir() / "results"

SHORT = {
    "representational_baseline": "1a",
    "representational_goal_directed": "1b",
    "syntactic_baseline": "2a",
    "syntactic_admissible": "2b",
    "syntactic_grammatical": "2c",
    "structural_typed": "3a",
    "structural_implicit": "3b",
    "structural_perturbed": "3p",
}


def rows(name, **where):
    path = RESULTS / f"{name}.json"
    data = json.loads(path.read_text())["rows"] if path.exists() else []
    return [r for r in data if all(r.get(k) == v for k, v in where.items())]


def mean(row, key):
    return statistics.mean(s[key] for s in row["sizes"])\
        if row["sizes"] else 0.


def percent(x):
    return f"{100 * x:.0f}%"
```

# Sampling string diagrams

*How should the property matrix of DisCoPy draw its terms?*

Internal seminar. Every number is read from `sampling/results/*.json`; the
detailed record is `sampling/analysis.md`.

<!---->

## Property testing in DisCoPy

- A **law** is a sequent, e.g.
  `unitality(f: Hom[A, B]) -> Equation[Hom[A, B]]`: draw `A`, `B`, then `f`,
  then check the equation.
- [Hypothesis](https://hypothesis.readthedocs.io) draws every value from a
  **choice sequence** and **shrinks** a counterexample by shrinking the
  sequence: shrinking comes with any sampler, as long as the smallest
  choices build the simplest terms.
- The matrix: about a hundred categories × their laws, 2,500 cells.
- A green cell says the law held **on what was drawn**: the sampler is our
  prior on where the bugs are.

<!---->

## What it found so far

From `retrospective.md`, compiled from the history of both repositories:

- **35** bugs found by the matrix and fixed, **15** more filed and ruled on,
  **82** laws declared broken, mostly where the checker is incomplete.
- The commonest: factory and dispatch bindings, serialisation, wrong
  assumptions about normal forms, coherence.
- Never found: **numeric limits**, e.g. the 52 indices of `einsum`
  (discopy/discopy#447): every sampler draws small diagrams.

<!---->

## Combinatorics in one slide

- A **combinatorial class** is a set with a size and finitely many objects
  of each size $n$, counted by its **generating function**
  $C(z) = \sum_n c_n z^n$.
- Constructions become equations: union is $+$, pairs are $\times$, e.g.
  binary trees $B = 1 + z B^2$, counted by the Catalan numbers.
- Labelled objects, e.g. permutations, take the exponential one,
  $\sum_n n! \frac{z^n}{n!} = \frac{1}{1 - z}$.
- Flajolet and Sedgewick, *Analytic Combinatorics* (2009).

<!---->

## Boltzmann sampling

Duchon, Flajolet, Louchard and Schaeffer (2004): draw $\gamma$ with
probability $\mathbb{P}_z(\gamma) = z^{|\gamma|} / C(z)$.

- **uniform at each size**;
- read off the specification: a union picks a branch with probability
  $A(z)/C(z)$, a product draws both sides independently;
- $z$ **tunes the expected size** $z C'(z)/C(z)$, up to the singularity
  $\rho$ of $C$;
- at $z = \rho$, **critical**, sizes follow a power law.

Bendkowski, Bodini and Dovgal (2018): one parameter per kind of node, and
tuning them all to expected counts is a **convex problem**.

<!---->

## Eight samplers

Each is a method `strategy_<sampler>` of the classes it makes sense for;
`PROPTEST_SAMPLER=<sampler>` runs the whole matrix under it.

| | sampler | a diagram is… |
|---|---|---|
| 1a | `representational_baseline` | independent layers, rejected unless they compose |
| 1b | `representational_goal_directed` | each layer from the codomain of the last |
| 2a | `syntactic_baseline` | a derivation tree of the rules, `fuel` deep |
| 2b | `syntactic_admissible` | the same without the admissible rules |
| 2c | `syntactic_grammatical` | a Boltzmann derivation of the rules at bounded width |
| 3a | `structural_typed` | typed boxes, then a wiring of equal types |
| 3b | `structural_implicit` | a wiring, which implies the boxes |
| 3p | `structural_perturbed` | a 3a normal form, rewritten up to coherence |

<!---->

## Syntactic: rules as a grammar

- A rule is a sequent, e.g. `cut(f: Hom[A, B], g: Hom[B, C]) -> Hom[A, C]`.
- **2c** instantiates every rule at every type of width ≤ 3 over two atoms:
  a context-free grammar, one nonterminal per pair of types, 225 of them,
  about seven thousand productions.
- Its generating function solves a polynomial system: Newton's method from
  zero, bisection for $\rho$ and for the expected size.
- **No rejection by construction**, and a fixed signature is just a grammar
  with fewer generators.

<!---->

## Structural: plumbing as a combinatorial class

| doctrine | plumbing | class | status |
|---|---|---|---|
| symmetric | each output feeds one input | matchings | 3a |
| markov | each input reads one output | functions | 3a |
| compact | each port pairs with another | Brauer diagrams | 3a |
| braided | strands | braid words | round two |
| pivotal | non-crossing pairings | Temperley–Lieb | round two |
| hypergraph | ports in spiders | cospans, partitions | round two |

<!---->

```python {.marimo hide_code="true"}
def validity_figure():
    data = rows("throughput", doctrine="symmetric")
    names = list(dict.fromkeys(r["sampler"] for r in data))
    figure, (left, right) = plt.subplots(1, 2, figsize=(9, 2.6))
    for offset, boundary in ((-0.2, "free"), (0.2, "fixed")):
        chosen = [next(r for r in data if r["sampler"] == n
                       and r["boundary"] == boundary) for n in names]
        x = np.arange(len(names)) + offset
        left.bar(x, [r["valid"] / r["cases"] for r in chosen], 0.4,
                 label=boundary)
        right.bar(x, [r["valid"] / r["seconds"] for r in chosen], 0.4)
    for ax, title in ((left, "valid share of test cases"),
                      (right, "valid diagrams per second")):
        ax.set_xticks(range(len(names)), [SHORT[n] for n in names])
        ax.set_title(title, fontsize=9)
    left.legend(fontsize=8)
    figure.tight_layout()
    return figure


fixed_1a = rows("throughput", sampler="representational_baseline",
                boundary="fixed")
mo.vstack([
    mo.md("## Finding 1: rejection is the baseline's only problem"),
    validity_figure() if rows("throughput") else mo.md("no results"),
    mo.md(f"""
- **1a never meets a fixed boundary**: {sum(r['valid'] for r in fixed_1a)}
  valid in {sum(r['cases'] for r in fixed_1a)} test cases, and under it the
  matrix is green on one to three distinct terms per law: **vacuous**.
- Every other sampler meets its boundary by construction; what Hypothesis
  still drops is its own **overruns**, as for any strategy.
- Building each strategy once made sampling **2.5 times faster** (200
  diagrams of 2a: 2.2s, then 0.9s): Hypothesis compiles every
  `@st.composite` defined inside a call.
"""),
])
```

```python {.marimo hide_code="true"}
def histograms():
    data = rows("throughput", doctrine="symmetric", boundary="fixed")
    figure, axes = plt.subplots(
        1, len(data), figsize=(1.3 * len(data), 2.2), sharey=True)
    for ax, row in zip(axes, data):
        ax.hist([s["boxes"] for s in row["sizes"]], bins=range(0, 16))
        ax.set_title(SHORT[row["sampler"]], fontsize=9)
    figure.supxlabel("boxes", fontsize=9)
    figure.tight_layout()
    return figure


compact_3a = rows("throughput", doctrine="compact",
                  sampler="structural_typed", boundary="fixed")
merged = max((1 - r["coherent"] / r["distinct"]
              for r in rows("throughput", boundary="fixed")
              if r["sampler"].startswith("syntactic") and r["distinct"]),
             default=0)
mo.vstack([
    mo.md("## Finding 2: each family draws its own diagrams"),
    histograms() if rows("throughput") else mo.md("no results"),
    mo.md(f"""
- **Syntactic** samplers have a tail of large diagrams, and write the same
  diagram in several ways: coherence merges up to
  {percent(merged)} of their distinct draws.
- **Structural** samplers draw normal forms with many crossings, e.g.
  {mean(compact_3a[0], 'crossings') if compact_3a else 0:.0f} per compact
  diagram under 3a, and only they put two boxes in one layer.
- **Representational** samplers draw at most one swap per layer.
"""),
])
```

```python {.marimo hide_code="true"}
symmetric_boltzmann = rows("boltzmann", doctrine="symmetric")
uniforms = {r["strategy"]: r for r in rows("uniforms")}


def boltzmann_figure():
    finite = [r for r in symmetric_boltzmann if np.isfinite(r["size"])]
    sizes = sorted({r["size"] for r in finite})
    figure, ax = plt.subplots(figsize=(4.5, 2.6))
    ax.plot(sizes, [next(r["generators"] for r in finite if r["size"] == s)
                    for s in sizes], "k--", label="theory")
    for exact, label in ((True, "exact seed"), (False, "Hypothesis choices")):
        ax.plot(sizes, [mean(next(r for r in finite if r["size"] == s
                                  and r["exact"] == exact), "boxes")
                        for s in sizes], "o-", label=label)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("expected nodes", fontsize=9)
    ax.set_ylabel("mean generators", fontsize=9)
    ax.legend(fontsize=8)
    figure.tight_layout()
    return figure


low = uniforms.get("integers(0, 2**20)", {}).get("below 0.01", 0)
mo.vstack([
    mo.md("## Finding 3: Hypothesis is not a Boltzmann sampler"),
    mo.hstack([
        boltzmann_figure() if symmetric_boltzmann else mo.md("no results"),
        mo.md(f"""
- Tuning works: drawn from a seed, the mean follows the theory, up to the
  cap on derivation size.
- Hypothesis puts **{percent(low)}** of `integers(0, 2**20)` in the lowest
  1%: it favours the first production, the identity.
- It also **cuts the tail**: it bounds the length of every example, and of
  the first ones much more.
- Exact sampling means **no shrinking**: its choices are a seed.
"""),
    ]),
])
```

```python {.marimo hide_code="true"}
convex = rows("convex")
convex_table = [{
    "kind": kind, "target": convex[0]["targets"][kind],
    "tuned": round(convex[0]["tuned"][kind], 2),
    "size alone": round(convex[0]["plain"][kind], 2)}
    for kind in ("node", "generator", "braiding", "trace_right")]\
    if convex else []
mo.vstack([
    mo.md("## Finding 4: convex tuning controls each kind of node"),
    mo.ui.table(convex_table, selection=None, show_column_summaries=False)
    if convex else mo.md("no results"),
    mo.md(f"""
- `cvxpy` tunes four parameters of the whole symmetric grammar in
  {convex[0]['seconds'] if convex else 0:.1f}s; counted on derivations drawn
  outside Hypothesis.
- It needs a specification: 2c has one, 3a could (matchings have an
  exponential generating function), the others are defined by their code.
"""),
])
```

```python {.marimo hide_code="true"}
mutants = rows("mutants")
mutant_names = list(dict.fromkeys(r["mutant"] for r in mutants if r["mutant"]))
mutant_samplers = list(dict.fromkeys(r["sampler"] for r in mutants))


def killed(mutant):
    return [SHORT[r["sampler"]] for r in mutants
            if r["mutant"] == mutant and r["kill"]]


def missed(mutant):
    return [SHORT[r["sampler"]] for r in mutants
            if r["mutant"] == mutant and not r["kill"]]


def kill_figure():
    grid = np.array([[next((1. if r["kill"] else 0.) for r in mutants
                           if r["mutant"] == m and r["sampler"] == s)
                      for s in mutant_samplers] for m in mutant_names])
    figure, ax = plt.subplots(figsize=(6, 2.4))
    ax.imshow(grid, cmap="Greens", vmin=0, vmax=1.4, aspect="auto")
    ax.set_xticks(range(len(mutant_samplers)),
                  [SHORT[s] for s in mutant_samplers])
    ax.set_yticks(range(len(mutant_names)), mutant_names, fontsize=8)
    for i, m in enumerate(mutant_names):
        for j, s in enumerate(mutant_samplers):
            row = next(r for r in mutants
                       if r["mutant"] == m and r["sampler"] == s)
            ax.text(j, i, row["kill"]["examples"] if row["kill"] else "—",
                    ha="center", va="center", fontsize=7)
    ax.set_title("examples until the first failing law", fontsize=9)
    figure.tight_layout()
    return figure


mo.vstack([
    mo.md("## Finding 5: planted bugs"),
    kill_figure() if mutants else mo.md("not run yet"),
    mo.md(f"""
- One line of DisCoPy rewritten per mutant; smallest counterexamples by
  hand in the analysis.
- **A permutation read as its inverse** is only found by
  {", ".join(killed("permutation_convention"))}: {", ".join(missed(
  "permutation_convention"))} never draw a cycle of three wires.
- Some bugs are found whatever is drawn: the law of yanking builds the
  left trace it checks.
- **One bug hides another**: under {", ".join(missed("identity_string"))},
  `str_transparency` already fails, so the empty string of the identity goes
  unseen.
- **A bug in the code a sampler runs crashes the sampler**, e.g. reading a
  hypergraph back under 3a and 3p.
"""),
])
```

```python {.marimo hide_code="true"}
semantic = rows("semantic", boundary="fixed")
mo.vstack([
    mo.md("## Finding 6: a fixed signature needs a grammar"),
    mo.ui.table([{
        "sampler": SHORT[r["sampler"]],
        "test cases per valid diagram": round(r["cases"] / max(r["valid"], 1)),
        "distinct tensors": r["tensors"]} for r in semantic],
        selection=None, show_column_summaries=False, page_size=8)
    if semantic else mo.md("not run yet"),
    mo.md("""
Five boxes over two atoms, evaluated as integer tensors, from `a` to
`a @ a`: the samplers that invent a box to close a boundary reject most of
what they draw; the grammar of 2c only has the boxes of the signature.
"""),
])
```

## Finding 7: a green cell can be a blind spot

Under 3a, `str_transparency` fails on symmetric diagrams:

```python
f, g = Box('f', x, x), Box('g', y, y)
d = Diagram(inside=(Layer(f, g), ), dom=x @ y, cod=x @ y)
assert str(d) == "f @ g" and eval(str(d)) != d   # two layers, not one
```

- A known limitation, declared broken on markov only: the default samplers
  of symmetric diagrams never put two boxes in a layer.
- It cannot just be declared broken there: a broken law is a strict xfail,
  so a sampler that misses it fails the cell. **Which sampler a law runs
  under is part of what the law claims.**

<!---->

## Open questions, where they stand

| question | answer so far |
|---|---|
| What does Boltzmann sampling buy us? | control of the size and of each kind of node, no rejection over a fixed signature; not uniformity over diagrams |
| Convex tuning beyond the grammar? | wherever there is a specification: 3a in principle |
| Critical sampling for `explore`? | only drawn from a seed: through Hypothesis the tail is cut |
| A class for each doctrine's plumbing? | matchings, functions, Brauer done; braids, Temperley–Lieb, cospans next |
| Semantic categories? | the grammar, alone without rejection |
| Normal or non-normal forms? | both: cycles of wires need structural samplers, which crash on the code they run; a mixture per law |

<!---->

## Next

1. The `--full` run, then a default sampler per doctrine, maybe a mixture.
2. `str_transparency` on symmetric diagrams: up to interchange, or a
   transparent `str` for layers of several boxes.
3. Counterexamples as regression tests: `Axiom.examples`, once per cell.
4. Round two: braided, pivotal, frobenius, and the tuning of 3a.
