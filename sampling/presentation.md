---
title: Sampling string diagrams
marimo-version: 0.23.16
layout_file: layouts/presentation.slides.json
---

```python {.marimo}
import json
import statistics

import marimo as mo
import matplotlib.pyplot as plt

RESULTS = mo.notebook_dir() / "results"


def load(name):
    path = RESULTS / f"{name}.json"
    return json.loads(path.read_text())["rows"] if path.exists() else []
```

# Sampling string diagrams

*How should the property matrix of DisCoPy draw its terms?*

Internal seminar, work in progress: every number here is read from
`sampling/results/*.json`, written by `sampling/experiments.py --quick`.

<!---->

## Property testing in one slide

- A **law** is a sequent, e.g. `unitality(f: Hom[A, B]) -> Equation[Hom[A, B]]`:
  draw `A`, `B`, then `f`, then check the equation.
- [Hypothesis](https://hypothesis.readthedocs.io) draws every value from a
  **choice sequence** (integers, booleans) and **shrinks** a counterexample by
  shrinking that sequence: whatever the sampler, shrinking comes for free as
  long as the smallest choices build the simplest terms.
- The matrix: 106 categories × their laws ≈ 2,500 cells, see
  `discopy/testable.py`.
- A green cell says the law held **on what was drawn**: the sampler is the
  prior on where bugs live.

<!---->

## What property testing has found so far

From `sampling/retrospective.md`, compiled from the git history:

- **35** bugs found by the matrix and fixed, **15** more filed and ruled on,
  **82** laws declared broken (mostly the checker's own incompleteness).
- Largest classes: factory / dispatch bindings (14), serialisation (9),
  wrong normal-form assumptions, coherence.
- Never found: **numeric limits**, e.g. the 52-index limit of `einsum`
  (discopy/discopy#447), because every strategy draws small diagrams.

<!---->

## Combinatorics background

- A **combinatorial class** $\mathcal{C}$ is a set with a size, finitely many
  objects of each size $n$: $c_n$.
- Its **generating function** $C(z) = \sum_n c_n z^n$ turns constructions
  into equations: disjoint union is $+$, pairs are $\times$, sequences are
  $\frac{1}{1 - A(z)}$.
- E.g. binary trees $B = 1 + z B^2$, so $b_n$ is the Catalan number.
  Permutations grow too fast, $\sum n! z^n$ diverges: labelled objects take
  the exponential generating function $\sum n! \frac{z^n}{n!} = \frac{1}{1-z}$.
- Flajolet, Sedgewick, *Analytic Combinatorics* (2009).

<!---->

## Boltzmann sampling

Duchon, Flajolet, Louchard, Schaeffer (2004): draw $\gamma \in \mathcal{C}$
with probability

$$\mathbb{P}_x(\gamma) = \frac{x^{|\gamma|}}{C(x)}$$

- **uniform at each size**: two objects of the same size are equally likely;
- the sampler is read off the specification: a union picks a branch with
  probability $A(x)/C(x)$, a product draws both sides independently;
- the parameter $x < \rho$ (the singularity of $C$) **tunes the expected
  size** $\mathbb{E}_x|\gamma| = x C'(x) / C(x)$;
- at $x = \rho$ (**critical**), sizes are heavy-tailed, e.g.
  $\mathbb{P}(|\gamma| = n) \sim n^{-3/2}$ for trees.

<!---->

## Tuning as convex optimisation

Bendkowski, Bodini, Dovgal (2018): with several parameters $x_1, \dots, x_k$,
one per kind of atom (boxes, swaps, spiders…), choosing the $x_i$ so that
each expected count hits a target is a **convex** problem in $\log x_i$.

- It applies to any class given by an algebraic or rational specification,
  i.e. a grammar.
- Open: does it apply beyond the grammar (2c)? (later slide)

<!---->

## Eight samplers

Each is a method `strategy_<sampler>` on the classes where it makes sense:
`Arrow.strategy` calls the one named by `Arrow.sampler`, and
`PROPTEST_SAMPLER=<sampler>` switches the whole matrix to it.

| | sampler | idea | status |
|---|---|---|---|
| 1a | `representational_baseline` | independent layers, rejected unless they compose | done |
| 1b | `representational_goal_directed` | each layer from the codomain of the last | done |
| 2a | `syntactic_baseline` | derivation trees of every rule (`search`) | existing |
| 2b | `syntactic_admissible` | the same without admissible rules | planned |
| 2c | `syntactic_grammatical` | rules instantiated at bounded width, a grammar | planned |
| 3a | `structural_typed` | typed boxes, then a matching of equal types | done |
| 3b | `structural_implicit` | the wiring, then the boxes it implies | existing |
| 3+ | `structural_perturbed` | a normal form, then random structural rewrites | planned |

<!---->

## 1. Representational

A diagram is how it is encoded: a list of layers `left @ box @ right`.

- **1a** draws each layer independently, then rejects the list unless
  consecutive layers compose and the boundaries are the ones asked for.
- **1b** splits the codomain so far as `left @ dom @ right` and draws a
  box (or a permutation) from `dom`, so every layer composes; a final box
  closes the codomain if asked for.
- Both are the encoding itself: whatever they draw, the encoding can hold,
  including non-normal forms such as an identity permutation split over two
  layers.

<!---->

## 2. Syntactic

A diagram is a **derivation tree** of the rules of its category, e.g.
`cut`, `mix`, `braiding`, `trace_left`: `FreeCategory.search` picks a rule
uniformly, binds its conclusion to the boundary asked for, draws its premises
with one less unit of `fuel`, and glues a fresh box to any side it misses.

- **2b** drops the admissible rules (derivable from the others), so the
  same diagram has fewer derivations.
- **2c** bounds the width of every boundary: then each rule has finitely
  many instances and the whole is a **context-free grammar**, which a
  Boltzmann sampler draws from with no rejection, tuned by convex
  optimisation.

<!---->

## 3. Structural

A diagram is its **normal form** up to the coherence theorem of its
doctrine: what remains is boxes and a combinatorial description of the
plumbing.

| doctrine | plumbing | combinatorial class |
|---|---|---|
| symmetric | wires between ports of equal type | bijections (matchings) |
| braided | strands | braid group words |
| markov | each input reads one output | functions |
| compact | each port pairs with one other | perfect matchings (Brauer) |
| pivotal / planar | non-crossing pairings | Temperley–Lieb / Catalan |
| hypergraph | ports in spiders | cospans of finite sets, i.e. partitions |

- **3a** draws typed boxes, then a random matching of equal types.
- **3b** draws the wiring port by port and lets it imply the domain of
  each box: the existing `Hypergraph.strategy`.

<!---->

## Metrics

- **size**: generators, layers, widest boundary, crossings (inversions of
  each permutation), other structural boxes;
- **rejection**: test cases Hypothesis gave up on, by reason: a failed
  `assume` is the sampler's rejection, an *overrun* is Hypothesis's own budget
  (about 10% even for `lists(integers())`);
- **speed**: valid diagrams per second;
- **distinct shapes**: diagrams up to the names of their fresh boxes;
- **the matrix**: each cell of a doctrine run under each sampler, seed 0;
- later: shrinking, planted bugs, semantic categories.

<!---->

```python {.marimo}
throughput = load("throughput")


def mean(row, key):
    sizes = row["sizes"]
    return statistics.mean(s[key] for s in sizes) if sizes else float("nan")


def rejected(row):
    return sum(v for k, v in row["gave_up"].items() if "assume" in k)


mo.vstack([
    mo.md("## Throughput: 200 examples per cell"),
    mo.ui.table([{
        "doctrine": row["doctrine"],
        "sampler": row["sampler"],
        "boundary": row["boundary"],
        "valid": f"{row['valid']}/{row['cases']}",
        "rejected": rejected(row),
        "per second": round(row["valid"] / row["seconds"]),
        "boxes": round(mean(row, "boxes"), 1),
        "max boxes": max((s["boxes"] for s in row["sizes"]), default=0),
        "crossings": round(mean(row, "crossings"), 2),
        "distinct": row["distinct"],
    } for row in throughput], page_size=12, selection=None),
])
```

```python {.marimo}
def histograms(doctrine, boundary):
    rows = [r for r in throughput
            if r["doctrine"] == doctrine and r["boundary"] == boundary]
    figure, axes = plt.subplots(
        1, len(rows), figsize=(3 * len(rows), 2.4), sharey=True)
    for ax, row in zip(axes, rows):
        ax.hist([s["boxes"] for s in row["sizes"]],
                bins=range(0, 18), color="#4c72b0")
        ax.set_title(row["sampler"].replace("_", "\n"), fontsize=8)
        ax.set_xlabel("boxes")
    figure.tight_layout()
    return figure


mo.vstack([
    mo.md("## Sizes: symmetric diagrams from `a @ b` to `b @ c`"),
    histograms("symmetric", "fixed") if throughput else mo.md("no results"),
])
```

## Throughput: what we read

- **1a is unusable with a boundary**: 0 valid of 459 test cases in every
  doctrine, and with free boundaries it only keeps lists of 0–2 layers:
  a longer list of independent layers almost never composes.
- **1b** never rejects and is among the fastest, but draws almost no
  crossings: one permutation per layer, chosen with no regard to types.
- **2a** is the slowest that works (about 20–30 per second) and the only one
  with a tail: up to 16 boxes from `fuel = 3`.
- **3a** draws the most crossings, by far on compact diagrams: matching
  typed ports over wide boundaries permutes a lot.
- **3b** is the fastest with structure, about 50 per second.
- Every sampler is **slow**: under 100 diagrams per second, and 10–35% of
  draws repeat a shape. Where the time goes is the next thing to profile.

<!---->

```python {.marimo}
matrix = load("matrix")


def outcomes(row):
    counts = {}
    for cell in row["cells"].values():
        counts[cell["outcome"]] = counts.get(cell["outcome"], 0) + 1
    return counts


def unsatisfiable(row):
    return sum("Unsatisfiable" in (cell["message"] or "")
               for cell in row["cells"].values())


mo.vstack([
    mo.md("## The matrix of symmetric diagrams under each sampler"),
    mo.ui.table([{
        "sampler": row["sampler"],
        "seconds": round(row["seconds"]),
        **outcomes(row),
        "unsatisfiable": unsatisfiable(row),
    } for row in matrix], selection=None) if matrix
    else mo.md("*not run yet*"),
])
```

## The matrix: what we read

- **A green cell can be vacuous.** Under 1a, all 45 laws pass, but on 1 to 3
  distinct terms: Hypothesis only raises `Unsatisfiable` when *no* example is
  valid. The distinct count of the report is what tells.
- **A green cell can be a blind spot.** Under 3a, `str_transparency` fails
  on symmetric diagrams:

```python
f, g = Box('f', x, x), Box('g', y, y)
d = Diagram(inside=(Layer(f, g), ), dom=x @ y, cod=x @ y)
assert str(d) == "f @ g" and eval(str(d)) != d   # two layers, not one
```

  A known limitation (`STR_SPLITS_LAYERS`), declared broken on markov only:
  the default samplers of symmetric diagrams never put two boxes in a layer.
  It cannot simply be declared broken there, since a broken law is a
  *strict* xfail: the default sampler would not find it and the cell would
  fail. Which sampler a law runs under is part of what the law claims.

<!---->

## Open questions

| question | experiment | current answer |
|---|---|---|
| What does Boltzmann sampling buy us? | size control, coverage of distinct shapes per budget, against 2a | open: needs 2c |
| Can we tune by convex optimisation beyond the grammar? | multi-parameter tuning of 3a with `cvxpy`: boxes, crossings | open |
| Critical or size-bounded? | heavy-tailed sizes on the `explore` profile, overruns as a metric | **critical** for `explore`, bounded for `pr` |
| Which class for each doctrine's plumbing? | table of the structural slide, one sampler per row | symmetric and compact done |
| Which samplers work on semantic categories? | sampling over a fixed signature, then a functor into `Matrix[int]` | open |
| Normal or non-normal forms? | per law: which sampler finds which planted bug | open |
| Pairs of equal diagrams? | `structural_perturbed`: random rewrites in context | open |

<!---->

## Next

1. **2b, 2c** with Boltzmann tuning, **3a** for markov and compact,
   `structural_perturbed`.
2. Planted bugs: for each sampler, a law and a mutation of DisCoPy it
   hardly finds, and the smallest counterexample, found by hand.
3. Semantic sampling on `Matrix[int]`, convex tuning, critical sampling.
4. Then choose the default sampler of each doctrine from the results.
