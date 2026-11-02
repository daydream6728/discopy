---
title: Sampling string diagrams, the analysis
marimo-version: 0.23.16
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


def load(name):
    path = RESULTS / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else {"rows": []}


def mean(row, key):
    sizes = row["sizes"]
    return statistics.mean(s[key] for s in sizes) if sizes else 0.


def rows(name, **where):
    return [r for r in load(name)["rows"]
            if all(r.get(k) == v for k, v in where.items())]


def percent(x):
    return f"{100 * x:.0f}%"
```

# Sampling string diagrams: the analysis

The detailed record of the experiments behind `presentation.md`. Every
number is read from `sampling/results/*.json`, written by

```
uv run --with cvxpy python sampling/experiments.py --quick
```

and the notebook never runs an experiment. The planted bugs are in
`mutants.py`, the bugs property testing found so far in `retrospective.md`.
To look at the draws of one sampler, run the playground:
`uv run marimo edit sampling/playground.py`.

<!---->

## 1. What is compared

Eight samplers, each a method `strategy_<sampler>` of the classes it makes
sense for; `Arrow.sampler` names the default and `PROPTEST_SAMPLER` switches
the whole property matrix.

| | sampler | a diagram is… | defined on |
|---|---|---|---|
| 1a | `representational_baseline` | independent layers, rejected unless they compose | monoidal |
| 1b | `representational_goal_directed` | each layer from the codomain of the last | monoidal, permutations in symmetric |
| 2a | `syntactic_baseline` | a derivation tree of every rule, `fuel` deep | every free category |
| 2b | `syntactic_admissible` | the same without the admissible rules | every free category |
| 2c | `syntactic_grammatical` | a Boltzmann derivation of the rules at width ≤ 3 | monoidal and below |
| 3a | `structural_typed` | typed boxes, then a random wiring of equal types | symmetric and below |
| 3b | `structural_implicit` | a random wiring, which implies the boxes | symmetric and below |
| 3p | `structural_perturbed` | a 3a normal form, rewritten up to coherence | symmetric and below |

The doctrines of round one are monoidal, symmetric, markov and compact, one
for each class of plumbing: none, permutations, functions and pairings.

<!---->

```python {.marimo hide_code="true"}
def throughput_figure(doctrine):
    data = rows("throughput", doctrine=doctrine)
    names = [r["sampler"] for r in data if r["boundary"] == "free"]
    figure, (left, right) = plt.subplots(1, 2, figsize=(9, 2.6))
    for offset, boundary in ((-0.2, "free"), (0.2, "fixed")):
        chosen = [next(r for r in data if r["sampler"] == name
                       and r["boundary"] == boundary) for name in names]
        x = np.arange(len(names)) + offset
        left.bar(x, [r["valid"] / r["cases"] for r in chosen], 0.4,
                 label=boundary)
        right.bar(x, [r["valid"] / r["seconds"] for r in chosen], 0.4,
                  label=boundary)
    for ax, title in ((left, "valid share of test cases"),
                      (right, "valid diagrams per second")):
        ax.set_xticks(range(len(names)), [SHORT[n] for n in names])
        ax.set_title(title, fontsize=9)
    left.legend(fontsize=8)
    figure.tight_layout()
    return figure


symmetric_rows = rows("throughput", doctrine="symmetric")
fixed_1a = [r for r in rows("throughput", sampler="representational_baseline",
                            boundary="fixed")]
overruns = [r["gave_up"].get("overrun", 0) / r["cases"]
            for r in load("throughput")["rows"]
            if r["sampler"] != "representational_baseline"]
mo.vstack([
    mo.md("## 2. Validity and speed"),
    throughput_figure("symmetric") if symmetric_rows else mo.md("no results"),
    mo.md(f"""
- **1a never meets a fixed boundary**: {sum(r['valid'] for r in fixed_1a)}
  valid diagrams in {sum(r['cases'] for r in fixed_1a)} test cases over the
  four doctrines. With free boundaries it keeps only lists of 0 to 2 layers.
- Every other sampler meets its boundary by construction, gluing a box when
  it must; what Hypothesis still gives up on is mostly its own **overruns**,
  {percent(min(overruns, default=0))} to {percent(max(overruns, default=0))}
  of test cases, a share `lists(integers())` has too.
- Speeds are for the quick budget, on one machine, with other experiments
  running: compare them within a column only.
"""),
])
```

```python {.marimo hide_code="true"}
def size_table(doctrine, boundary):
    return [{
        "sampler": SHORT[r["sampler"]],
        "boxes": round(mean(r, "boxes"), 1),
        "max boxes": max((s["boxes"] for s in r["sizes"]), default=0),
        "crossings": round(mean(r, "crossings"), 1),
        "other structure": round(mean(r, "structural"), 1),
        "distinct": percent(r["distinct"] / max(r["valid"], 1)),
        "up to coherence": percent(r["coherent"] / max(r["valid"], 1)),
    } for r in rows("throughput", doctrine=doctrine, boundary=boundary)]


mo.vstack([
    mo.md("## 3. Size and diversity: symmetric diagrams from `a @ b` to "
          "`b @ c`"),
    mo.ui.table(size_table("symmetric", "fixed"), selection=None,
                show_column_summaries=False),
    mo.md("""
*Boxes* are the generators, those inside traces included; *crossings* the
inversions of the permutations; *distinct* the share of diagrams that differ
up to the names of their boxes, *up to coherence* up to the isomorphism of
their hypergraphs (a Weisfeiler-Lehman hash).
"""),
])
```

## Size and diversity: what we read

```python {.marimo hide_code="true"}
def row(doctrine, sampler, boundary="fixed"):
    found = rows("throughput", doctrine=doctrine, sampler=sampler,
                 boundary=boundary)
    return found[0] if found else {"sizes": [], "valid": 1, "coherent": 0,
                                   "distinct": 0}


compact_3a = row("compact", "structural_typed")
fixed = rows("throughput", boundary="fixed")


def merged(sampler):
    found = [r for r in fixed if r["sampler"] == sampler and r["valid"]]
    return max((1 - r["coherent"] / r["distinct"] for r in found), default=0)


def tail(sampler):
    return max((s["boxes"] for r in rows("throughput", sampler=sampler)
                for s in r["sizes"]), default=0)


def repeats(sampler):
    found = [r for r in fixed if r["sampler"] == sampler and r["valid"]]
    return max((1 - r["distinct"] / r["valid"] for r in found), default=0)


mo.md(f"""
- **Only the syntactic samplers have a tail**: up to {tail('syntactic_baseline')}
  boxes under 2a and {tail('syntactic_grammatical')} under 2c, while the layer
  and structural samplers stop at `fuel + 2` = 5 boxes plus a balancing one.
- **Crossings belong to the structural samplers**: matching typed wires
  permutes them, e.g. {mean(compact_3a, 'crossings'):.0f} crossings per
  compact diagram from `a @ b` to `b @ c` under 3a, against at most one per
  layer under 1b.
- **Coherence merges the draws that write one diagram twice**: up to
  {percent(merged('syntactic_baseline'))} of 2a's distinct draws,
  {percent(merged('syntactic_admissible'))} of 2b's and
  {percent(merged('structural_perturbed'))} of 3p's, against
  {percent(merged('structural_typed'))} of 3a's, which draws normal forms.
- **2c repeats itself most**: up to {percent(repeats('syntactic_grammatical'))}
  of its draws repeat another, since a Boltzmann distribution puts most of
  its mass on the smallest terms, see section 4.
""")
```

<!---->

## 4. Boltzmann sampling

The grammar of 2c instantiates every rule of the doctrine at every type of
width at most 3 over two atoms: 225 nonterminals, one for each pair of
types, and about seven thousand productions. Its generating function is the
least solution of a polynomial system, computed by Newton's method; the
singularity `rho` by bisection on where it diverges; the parameter `z` for
an expected number of nodes by bisection below `rho`.

```python {.marimo hide_code="true"}
def boltzmann_figure(doctrine):
    data = rows("boltzmann", doctrine=doctrine)
    finite = [r for r in data if r["size"] != float("inf")
              and np.isfinite(r["size"])]
    figure, (left, right) = plt.subplots(1, 2, figsize=(9, 2.8))
    sizes = sorted({r["size"] for r in finite})
    left.plot(sizes, [next(r["generators"] for r in finite
                           if r["size"] == s) for s in sizes],
              "k--", label="theory")
    for exact, label in ((True, "exact seed"), (False, "Hypothesis choices")):
        left.plot(sizes, [mean(next(r for r in finite if r["size"] == s
                                    and r["exact"] == exact), "boxes")
                          for s in sizes], "o-", label=label)
    left.set_xscale("log", base=2)
    left.set_xlabel("expected nodes")
    left.set_title("mean generators", fontsize=9)
    left.legend(fontsize=8)
    critical = [r for r in data if not np.isfinite(r["size"])]
    for r in critical:
        counts = np.bincount([s["boxes"] for s in r["sizes"]])
        right.loglog(np.nonzero(counts)[0] + 1, counts[counts > 0], "o",
                     label="exact seed" if r["exact"] else
                     "Hypothesis choices")
    right.set_xlabel("generators + 1")
    right.set_title("critical sampling: how many draws", fontsize=9)
    right.legend(fontsize=8)
    figure.tight_layout()
    return figure


symmetric_boltzmann = rows("boltzmann", doctrine="symmetric")
boltzmann_figure("symmetric") if symmetric_boltzmann else mo.md("no results")
```

```python {.marimo hide_code="true"}
uniform = {r["strategy"]: r for r in load("uniforms")["rows"]}


def share(name, q=0.01):
    return percent(uniform.get(name, {}).get(f"below {q}", 0))


critical_rows = [r for r in symmetric_boltzmann if not np.isfinite(r["size"])]
rejected = {r["exact"]: r["gave_up"].get("rejected", 0) / r["cases"]
            for r in critical_rows}
overrun = {r["exact"]: r["gave_up"].get("overrun", 0) / r["cases"]
           for r in critical_rows}
rho = symmetric_boltzmann[0]["rho"] if symmetric_boltzmann else 0
mo.md(f"""
### What we read

- **Theory and the exact sampler agree** while derivations stay under the
  cap of 200 nodes; above it, the rare large draws that carry the mean are
  rejected, so the mean saturates. For symmetric diagrams
  `rho = {rho:.4f}`.
- **Hypothesis does not draw what Boltzmann asks for.** A choice of
  production is a number in `[0, 1)`. Hypothesis puts
  {share('integers(0, 2**20)')} of `integers(0, 2**20)` in the lowest 1%,
  {share('floats(0, 1)')} of `floats(0, 1)`, {share('a byte among 20')} of a
  byte drawn among others and {share('randoms(true)')} of
  `randoms(use_true_random=True)`: Hypothesis favours the simplest choice,
  the first production, the identity. 2c draws bytes: biased, but little.
- **Hypothesis cuts the tail.** It caps the length of its first examples
  at five times that of the simplest one, and of every example by a fixed
  buffer: at the critical point it gives up on {percent(overrun.get(False, 0))}
  of test cases drawn by choices, against {percent(overrun.get(True, 0))}
  from a seed, which only the 200-node cap cuts
  ({percent(rejected.get(True, 0))} rejected).
- **The exact sampler does not shrink**: its choices are a seed. The
  shrinkable one samples a Boltzmann distribution conditioned on fitting
  Hypothesis's buffer, which is smaller than asked for.
- **Most derivations are tiny either way.** Tuning moves the mean, not the
  median: a Boltzmann distribution near its singularity is a power law,
  and the grammar is ambiguous, e.g. `f >> id` and `f` are two derivations
  of one diagram, so its uniformity is over derivations, not diagrams.
""")
```

<!---->

## 5. Tuning as convex optimisation

```python {.marimo hide_code="true"}
convex = load("convex")["rows"]
if convex:
    result = convex[0]
    table = [{"kind": kind, "target": result["targets"][kind],
              "tuned": round(result["tuned"][kind], 2),
              "size alone": round(result["plain"][kind], 2)}
             for kind in ("node", "generator", "braiding", "trace_right")]
    content = mo.vstack([
        mo.ui.table(table, selection=None, show_column_summaries=False),
        mo.md(f"""
Following Bendkowski, Bodini and Dovgal (2018), the expected count of each
kind of production is the logarithmic derivative of the generating function
in its parameter, and choosing the parameters for given counts is a convex
problem in their logarithms: `cvxpy` solves it for the whole grammar in
{result['seconds']:.1f}s ({result['status']}), with `z = {result['z']:.4f}`
for `rho = {result['rho']:.4f}` and biases
{', '.join(f"{k} {v:.2f}" for k, v in result['bias'].items())}.

The counts are those of derivations drawn outside Hypothesis, with true
randomness, so only sampling noise and the few derivations past ten
thousand nodes left out separate them from their targets: each count moves
as its target asks, e.g.
{result['tuned']['braiding'] / result['plain']['braiding']:.0f} times more swaps, which tuning the size alone
cannot do. Through Hypothesis the counts shrink as in section 4.

**Beyond 2c**, tuning needs a specification whose generating function is
known: 3a draws boxes, then a matching of their wires, i.e. a labelled
product, whose exponential generating function exists, so its number of
boxes and of crossings (a Mallows distribution on matchings) could be tuned
the same way. 1b, 2a and 3b draw choices whose probabilities are not those
of any specification, so they cannot.
"""),
    ])
else:
    content = mo.md("no results")
content
```

<!---->

```python {.marimo hide_code="true"}
matrix = load("matrix")["rows"]


def matrix_summary(row):
    cells = row["cells"].values()
    counts = {}
    for cell in cells:
        counts[cell["outcome"]] = counts.get(cell["outcome"], 0) + 1
    vacuous = sum(cell["outcome"] == "passed"
                  and (cell["distinct"] or 0) <= 3 for cell in cells)
    return {"doctrine": row["doctrine"], "sampler": SHORT[row["sampler"]],
            "passed": counts.get("passed", 0),
            "of which on ≤ 3 terms": vacuous,
            "failed": counts.get("failed", 0),
            "seconds": round(row["seconds"])}


failures = sorted({(row["doctrine"], name.split(".")[-1], SHORT[row["sampler"]])
                   for row in matrix for name, cell in row["cells"].items()
                   if cell["outcome"] == "failed"})
mo.vstack([
    mo.md("## 6. The property matrix under each sampler"),
    mo.ui.table([matrix_summary(r) for r in matrix], selection=None,
                show_column_summaries=False, page_size=8)
    if matrix else mo.md("not run yet"),
    mo.md("Cells that fail: " + "; ".join(
        f"`{d}.{law}` under {s}" for d, law, s in failures) or "none"),
])
```

```python {.marimo hide_code="true"}
def vacuous(sampler):
    return sum(cell["outcome"] == "passed" and (cell["distinct"] or 0) <= 3
               for row in matrix if row["sampler"] == sampler
               for cell in row["cells"].values())


def checked(sampler):
    return sum(cell["outcome"] == "passed"
               for row in matrix if row["sampler"] == sampler
               for cell in row["cells"].values())


def failing(law):
    return [f"{d} under {s}" for d, name, s in failures if name == law]


mo.md(f"""
## The matrix: what we read

- **A green cell can be vacuous**: under 1a, {vacuous('representational_baseline')}
  of {checked('representational_baseline')} green cells drew at most three
  distinct terms, since Hypothesis only gives up when *no* example is valid,
  against {vacuous('representational_goal_directed')} under 1b: `twist_unit`
  in each doctrine with a twist, a law with nothing to draw. The distinct
  count of the report is what tells them apart.
- **A green cell can be a blind spot**: `str_transparency` fails
  ({"; ".join(failing("str_transparency"))}). On symmetric and compact
  diagrams a layer of two boxes prints as `f @ g`, which reads back as two
  layers, and only the structural samplers draw such layers; on compact ones
  under 1a, a lone rotated box `f.r` reads back only if `f` is defined,
  which the law documents as off its domain but does not assume away. Both
  are in `retrospective.md`. Neither can just be declared broken: a broken
  law is a strict xfail, so a sampler that misses it fails the cell.
- **Every other law holds under every sampler**: no new bug of DisCoPy was
  found in this run, which is what the planted bugs are for.
""")
```

<!---->

```python {.marimo hide_code="true"}
mutant_rows = load("mutants")["rows"]
names = [m for m in dict.fromkeys(
    r["mutant"] for r in mutant_rows if r["mutant"])]
samplers = list(dict.fromkeys(r["sampler"] for r in mutant_rows))


def cell(mutant, sampler):
    found = [r for r in mutant_rows
             if r["mutant"] == mutant and r["sampler"] == sampler]
    if not found or not found[0]["kill"]:
        return "—"
    kill = found[0]["kill"]
    return f"{kill['examples']} ({kill['law']})" if not kill["crash"]\
        else f"crash: {kill['crash']}"


mo.vstack([
    mo.md("## 7. Planted bugs: examples drawn until the first failing law"),
    mo.ui.table([{"mutant": m, **{SHORT[s]: cell(m, s) for s in samplers}}
                 for m in names], selection=None,
                show_column_summaries=False)
    if mutant_rows else mo.md("not run yet"),
    mo.md("""
Each mutant rewrites one line of DisCoPy (`mutants.py`). For each sampler,
the laws of symmetric diagrams are checked in order, 30 examples each, and
the first that fails kills the mutant; a law that fails without any mutant
under that sampler is left out. — means no law failed.
"""),
])
```

### The smallest counterexamples, by hand

| mutant | class | origin | smallest counterexample |
|---|---|---|---|
| `layer_offsets` | off-by-one | `Layer.boxes_and_offsets` counts the inputs of the boxes on the left, not their outputs | `Diagram(inside=(Layer(f, g), ), dom=x @ y, cod=y)` for `f = Box('f', x, Ty())`, `g = Box('g', y, y)`: one layer of two boxes, the left one changing the width |
| `permutation_convention` | wrong convention | a native `Permutation` is read as its inverse | `Permutation(x @ y @ z, [1, 2, 0])`: the smallest permutation that is not an involution |
| `layer_overlap` | `<` vs `<=` | reading a hypergraph back, a box joins the layer of the box before it although it starts on its last output | `Box('f', x, y) >> Box('g', y, x)`: two boxes in a row |
| `left_trace` | coherence | a trace on the left feeds back the last output, not the first | `Box('f', x, x @ y).trace(left=True)`: one box, its outputs of two types; with outputs of one type every law sees the same wrong wiring on both sides |
| `identity_string` | missing edge case | the identity prints as the empty string | `Id(x)` |

```python {.marimo hide_code="true"}
def shrunk(mutant):
    out = []
    for r in mutant_rows:
        if r["mutant"] == mutant and r["kill"] and not r["kill"]["crash"]:
            terms = r["kill"]["shrunk"]
            out.append((SHORT[r["sampler"]],
                        sum(t["boxes"] + t["structural"] for t in terms),
                        sum(t["layers"] for t in terms)))
    return out


mo.md("Shrunk by Hypothesis, as (sampler, boxes, layers) summed over the "
      "terms of the failing law: " + "; ".join(
          f"**{m}** " + ", ".join(f"{s} {b}/{l}" for s, b, l in shrunk(m))
          for m in names) if mutant_rows else "not run yet")
```

```python {.marimo hide_code="true"}
def killers(mutant, crash=None):
    return [SHORT[r["sampler"]] for r in mutant_rows
            if r["mutant"] == mutant and r["kill"]
            and (crash is None or bool(r["kill"]["crash"]) == crash)]


def survivors(mutant):
    return [SHORT[r["sampler"]] for r in mutant_rows
            if r["mutant"] == mutant and not r["kill"]]


def natural(sampler):
    return next((r["fails"] for r in mutant_rows if r["mutant"] is None
                 and r["sampler"] == sampler), [])


def listed(xs):
    return ", ".join(xs) or "none"


def sizes(mutant):
    return {s: (b, l) for s, b, l in shrunk(mutant)}


def largest(mutant):
    found = sizes(mutant)
    if not found:
        return "none"
    sampler = max(found, key=lambda s: sum(found[s]))
    boxes, layers = found[sampler]
    return f"{boxes} boxes over {layers} layers under {sampler}"


mo.md(f"""
## Planted bugs: what we read

- **Two boxes in a row** (`layer_overlap`) are found by
  {listed(killers('layer_overlap'))}; Hypothesis shrinks it to `f >> f`, the
  hand minimum, wherever the law fails rather than the sampler.
- **A permutation that is not an involution** (`permutation_convention`) is
  found by {listed(killers('permutation_convention'))} and missed by
  {listed(survivors('permutation_convention'))}, which never draw a cycle of
  three wires: their swaps are transpositions. The structural samplers shrink
  it to a cycle between two or three boxes; the largest shrunk counterexample,
  {largest('permutation_convention')}, is far from the lone `Permutation` by
  hand.
- **A layer of two boxes** (`layer_offsets`) is found by
  {listed(killers('layer_offsets'))}; only 3a shrinks it to the hand minimum,
  one layer `f @ f`, since only 3a draws such a layer itself: the others reach
  it through the foliation inside a law, the largest at
  {largest('layer_offsets')}.
- **A trace on the left** (`left_trace`) is found by
  {listed(killers('left_trace'))}, mostly through the law of yanking, which
  builds a left trace itself: whatever the sampler draws, the law checks it.
- **One bug hides another**: `identity_string` is missed by
  {listed(survivors('identity_string'))}, under which `str_transparency`
  already fails, so the only law that would catch it is out of the race.
- **A bug in the code a sampler runs crashes the sampler**: under
  {listed(sorted(set(sum((killers(m, True) for m in names), []))))}, reading
  a hypergraph back is part of drawing, so a mutant there is found as a crash
  of the sampler, with no law and no shrinking.
- **A first attempt at interlocked traces was an equivalent mutant**:
  feeding back a trace of two wires crossed changes nothing, since a trace
  of a symmetric diagram reaches the hypergraph one wire at a time. No
  sampler and no law can find a bug that cannot happen.
- **The historical numeric bug** (discopy/discopy#447, the 52 indices of
  `einsum`) needs a tensor of 52 wires: no sampler here draws one, and none
  should by default. A size limit is a law of its own, with its own sampler.
""")
```

<!---->

```python {.marimo hide_code="true"}
semantic = load("semantic")["rows"]
mo.vstack([
    mo.md("## 8. A fixed signature: symmetric diagrams as tensors"),
    mo.ui.table([{
        "sampler": SHORT[r["sampler"]], "boundary": r["boundary"],
        "valid": f"{r['valid']}/{r['cases']}",
        "distinct tensors": r["tensors"],
        "zero tensors": r["zero"],
        "boxes": round(mean(r, "boxes"), 1),
    } for r in semantic], selection=None, show_column_summaries=False,
        page_size=16) if semantic else mo.md("not run yet"),
    mo.md("""
Five boxes over two atoms `a` and `b`, of dimensions 2 and 3, each with a
random integer tensor; the types are drawn from `a` and `b` only and a box
of a type the signature lacks is rejected, since a semantic category cannot
invent it. The fixed boundary is `a -> a @ a`.
"""),
])
```

```python {.marimo hide_code="true"}
def semantic_row(sampler, boundary="fixed"):
    found = [r for r in semantic
             if r["sampler"] == sampler and r["boundary"] == boundary]
    return found[0] if found else {"cases": 0, "valid": 1, "tensors": 0}


def per_valid(sampler):
    r = semantic_row(sampler)
    return r["cases"] / max(r["valid"], 1)


mo.md(f"""
## A fixed signature: what we read

- **Samplers that invent boxes to meet a boundary break**: 1b, 2a, 2b and 3p
  glue a box to whatever type they end on, 3a and 3b balance their wiring
  with one, which a fixed signature seldom has, so they reject most of what
  they draw: to reach `a -> a @ a`, 3a takes
  {per_valid('structural_typed'):.0f} test cases for each valid diagram,
  2a {per_valid('syntactic_baseline'):.0f} and 1b
  {per_valid('representational_goal_directed'):.0f}.
- **2c does not**: its grammar only has the generators of the signature, so a
  boundary it can reach is reached, in
  {per_valid('syntactic_grammatical'):.1f} test cases per valid diagram, and
  one it cannot is known before any draw; it also finds the most distinct
  tensors there, {semantic_row('syntactic_grammatical')['tensors']}.
- **A semantic category has a smaller space** than its free one: the
  distinct tensors are fewer than the distinct diagrams, and diagrams with a
  delayed box, which 2a derives, have no tensor at all.
""")
```

<!---->

## 9. The open questions, where they stand

| question | answer so far | confidence |
|---|---|---|
| What does Boltzmann sampling buy us? | control of the mean size and of each kind of node, and a sampler with no rejection over a fixed signature; not uniformity over diagrams, since derivations are ambiguous | medium |
| Tuning as convex optimisation beyond 2c? | yes wherever there is a specification: 3a in principle; not for the samplers defined by their code | medium |
| Critical sampling for `explore`? | yes for the exact sampler, whose tail is real; through Hypothesis's choices the tail is cut, so critical sampling buys little there | medium |
| A combinatorial class for each doctrine? | symmetric: matchings; markov: functions; compact: Brauer pairings, all implemented in 3a; braided (braid words), pivotal (Temperley–Lieb) and frobenius (cospans) are round two | high |
| Semantic categories? | only the grammar respects a fixed signature without rejection | high |
| Normal or non-normal forms? | both: cycles of wires need the structural samplers, which draw normal forms, but those crash on bugs in the code they run themselves and hide bugs behind laws they break; a mixture per law covers both | medium |
| Pairs of equal diagrams? | 3p draws a rewritten normal form, which the laws already compare with its quotient; a law over pairs is a next step | low |

<!---->

## 10. What to do next

1. The `--full` run, then choose the default sampler of each doctrine,
   possibly a mixture, from these numbers.
2. Decide `str_transparency` on symmetric diagrams: compare up to
   interchange, print a layer of several boxes transparently, or choose the
   sampler per law.
3. Regression examples: `Axiom.examples`, run once per cell with
   `@example`, for every counterexample found so far.
4. Round two: braided, pivotal, frobenius, and the tuning of 3a.
