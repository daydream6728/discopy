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
    "syntactic_grammatical_admissible": "2bc",
    "portfolio": "mix",
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
sense for; `Arrow.default_strategy` names the default and `PROPTEST_SAMPLER` switches
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

Every level of the hierarchy of free categories is covered: the arrows of
`cat`, then the diagrams of monoidal, spacial, braided, balanced, ribbon,
rigid, pivotal, symmetric, feedback, markov, comarkov, frobenius, compact,
closed and biclosed. A sampler runs on every class it is a method of: the
syntactic ones everywhere, the representational and grammatical ones from
monoidal down, the structural ones from symmetric down. The planted bugs are
searched with the laws of symmetric diagrams, the convex tuning and the
fixed signature on symmetric diagrams too.

<!---->

```python {.marimo hide_code="true"}
def coverage_figure():
    data = rows("throughput", regime="natural", boundary="free")
    doctrine_names = list(dict.fromkeys(r["doctrine"] for r in data))
    sampler_names = list(SHORT)
    grid = np.full((len(doctrine_names), len(sampler_names)), np.nan)
    for r in data:
        grid[doctrine_names.index(r["doctrine"]),
             sampler_names.index(r["sampler"])] = r["valid"] / r["cases"]
    figure, ax = plt.subplots(figsize=(7, 0.32 * len(doctrine_names) + 1))
    ax.imshow(grid, cmap="Greens", vmin=0, vmax=1.2, aspect="auto")
    ax.set_xticks(range(len(sampler_names)),
                  [SHORT[n] for n in sampler_names], fontsize=8)
    ax.set_yticks(range(len(doctrine_names)), doctrine_names, fontsize=8)
    for i, row in enumerate(grid):
        for j, value in enumerate(row):
            if not np.isnan(value):
                ax.text(j, i, f"{value:.0%}", ha="center", va="center",
                        fontsize=6)
    ax.set_title("valid share of test cases, free boundaries; blank: the "
                 "sampler does not apply", fontsize=8)
    figure.tight_layout()
    return figure


mo.vstack([
    mo.md("## Coverage: every level of the hierarchy"),
    coverage_figure() if rows("throughput", regime="natural")
    else mo.md("not run yet"),
])
```

```python {.marimo hide_code="true"}
def throughput_figure(doctrine):
    data = rows("throughput", regime="natural", doctrine=doctrine)
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


symmetric_rows = rows("throughput", regime="natural", doctrine="symmetric")
fixed_1a = [r for r in rows("throughput", regime="natural", sampler="representational_baseline",
                            boundary="fixed")]
overruns = [r["gave_up"].get("overrun", 0) / r["cases"]
            for r in rows("throughput", regime="natural")
            if r["sampler"] != "representational_baseline"]
mo.vstack([
    mo.md("## 2. Validity and speed"),
    throughput_figure("symmetric") if symmetric_rows else mo.md("no results"),
    mo.md(f"""
- **1a almost never meets a fixed boundary**:
  {sum(r['valid'] for r in fixed_1a)} valid diagrams in
  {sum(r['cases'] for r in fixed_1a)} test cases over the four doctrines. With free boundaries it keeps only lists of 0 to 2 layers.
- Every other sampler meets its boundary by construction, gluing a box when
  it must; what Hypothesis still gives up on is mostly its own **overruns**,
  {percent(min(overruns, default=0))} to {percent(max(overruns, default=0))}
  of test cases, a share `lists(integers())` has too.
- Speeds are those of one core: each doctrine and sampler runs in its own
  process, as many at once as the machine has cores, so compare them
  within a run only, not across machines.
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
    } for r in rows("throughput", regime="natural", doctrine=doctrine, boundary=boundary)]


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
    found = rows("throughput", regime="natural", doctrine=doctrine, sampler=sampler,
                 boundary=boundary)
    return found[0] if found else {"sizes": [], "valid": 1, "coherent": 0,
                                   "distinct": 0}


compact_3a = row("compact", "structural_typed")
fixed = rows("throughput", regime="natural", boundary="fixed")


def merged(sampler):
    found = [r for r in fixed if r["sampler"] == sampler and r["valid"]]
    return max((1 - r["coherent"] / r["distinct"] for r in found), default=0)


def tail(sampler):
    return max((s["boxes"] for r in rows("throughput", regime="natural", sampler=sampler)
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

```python {.marimo hide_code="true"}
calibration = load("calibration")["rows"]


def reached(sampler, target, doctrine="symmetric"):
    found = [r for r in calibration if r["sampler"] == sampler
             and r["target"] == target and r["doctrine"] == doctrine]
    return found[0] if found else None


def matched_row(sampler, regime, doctrine="symmetric"):
    found = rows("throughput", doctrine=doctrine, sampler=sampler,
                 regime=regime, boundary="free")
    return found[0] if found else None


def matched_table():
    table = []
    for sampler in dict.fromkeys(r["sampler"] for r in calibration):
        three, six = reached(sampler, 3.), reached(sampler, 6.)
        natural = matched_row(sampler, "natural")
        at_three = matched_row(sampler, "matched 3")
        if not (three and natural and at_three):
            continue
        table.append({
            "sampler": SHORT[sampler],
            "own mean": round(mean(natural, "boxes"), 1),
            "largest mean": round(max(three["means"].values()), 1),
            "for 3 boxes": ", ".join(f"{k} = {v:g}"
                                     for k, v in three["params"].items()),
            "mean there": round(mean(at_three, "boxes"), 1),
            "up to coherence there": percent(
                at_three["coherent"] / max(at_three["valid"], 1)),
        })
    return table


short_of = [SHORT[r["sampler"]] for r in calibration
            if r["doctrine"] == "symmetric" and r["target"] == 3.
            and abs(r["mean"] - 3.) > .5]
mo.vstack([
    mo.md("## Matched sizes: symmetric diagrams with free boundaries"),
    mo.ui.table(matched_table(), selection=None,
                show_column_summaries=False) if calibration
    else mo.md("not run yet"),
    mo.md(f"""
Each sampler has one knob for its size, `fuel`, or the expected number of
nodes for 2c and 2bc; the calibration tries each value on free boundaries
and keeps the one whose mean number of boxes is nearest the target.

- **The knobs have a short range**: a derivation stops at a generator with a
  fixed probability at every node, so `fuel` deepens the tree without
  growing it much, and Hypothesis cuts the tail of 2c whatever its size, so
  {listed(short_of)} cannot reach a mean of 3 boxes and no sampler but the
  layered and structural ones comes near 6.
- **Matching sizes is therefore a control, not a regime**: it tells whether
  a sampler finds a bug because of what it draws or because it draws more,
  see the planted bugs.
"""),
])
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
- **A green cell can be a blind spot.** In the first runs
  `str_transparency` failed only under the structural samplers: a layer of
  two boxes prints as `f @ g`, which reads back as two layers, and only they
  draw such layers. The law now compares up to interchange, and following
  it up found three bugs that the default sampler never drew, a rotated box,
  a right closed evaluation and an identity spider whiskered into an empty
  layer: all fixed, see `retrospective.md`.
- **Cells that fail in this run**:
  {"; ".join(f"`{d}.{law}` under {s}" for d, law, s in failures) or "none"}.
""")
```

<!---->

```python {.marimo hide_code="true"}
mutant_rows = load("mutants")["rows"]
names = list(dict.fromkeys(r["mutant"] for r in mutant_rows))
samplers = list(dict.fromkeys(r["sampler"] for r in mutant_rows))
seeds = len({r["seed"] for r in mutant_rows})


def runs(mutant, sampler, regime="natural"):
    return [r for r in mutant_rows if r["mutant"] == mutant
            and r["sampler"] == sampler and r["regime"] == regime]


def rate(mutant, sampler, regime="natural", outcome="kill"):
    found = runs(mutant, sampler, regime)
    return sum(bool(r[outcome]) for r in found) / len(found)\
        if found else float("nan")


def cell(mutant, sampler):
    found = runs(mutant, sampler)
    kills = [r["examples"] for r in found if r["kill"]]
    crashes = sum(bool(r["crash"]) for r in found)
    text = f"{len(kills)}/{len(found)}"
    if kills:
        text += f" · {statistics.median(kills):g} ex."
    if crashes:
        text += f" · {crashes} crash"
    return text


mo.vstack([
    mo.md("## 7. Planted bugs: kills over seeds, examples until the first"),
    mo.ui.table([{"mutant": m, **{SHORT[s]: cell(m, s) for s in samplers}}
                 for m in names], selection=None,
                show_column_summaries=False)
    if mutant_rows else mo.md("not run yet"),
    mo.md(f"""
Each mutant rewrites one line of DisCoPy (`mutants.py`). Under each sampler
and each of {seeds} seeds, the laws of symmetric diagrams are searched in
order, {load("mutants")["mode"] == "quick" and 30 or 300} examples each, for
arguments on which a law **fails with the mutant and holds without it**: the
first such law kills the mutant. *k/n* is the share of seeds that killed it,
then the median number of examples drawn until then; a *crash* is the
sampler itself failing on the mutated code, which counts as no kill. All
samplers draw their types over the atoms `a` and `b`.
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
def killed(sampler, regime="natural"):
    rates = [rate(m, sampler, regime) for m in names]
    return sum(rates) / len(rates) if rates else float("nan")


def detected(sampler, regime="natural"):
    rates = [rate(m, sampler, regime) + rate(m, sampler, regime, "crash")
             for m in names]
    return sum(rates) / len(rates) if rates else float("nan")


def shrinking(sampler):
    kills = [r["kill"] for r in mutant_rows if r["sampler"] == sampler
             and r["regime"] == "natural" and r["kill"]]
    if not kills:
        return {}
    return {
        "shrunk terms": statistics.median(
            sum(t["boxes"] + t["structural"] + t["layers"]
                for t in k["shrunk"]) for k in kills),
        "shrinking calls": statistics.median(
            k["shrink_calls"] for k in kills),
        "shrinking seconds": round(statistics.median(
            k["shrink_seconds"] for k in kills), 2)}


def glue(sampler):
    asked = sum(r["glue"]["asked"] for r in mutant_rows
                if r["sampler"] == sampler)
    glued = sum(r["glue"]["glued"] for r in mutant_rows
                if r["sampler"] == sampler)
    return glued / asked if asked else None


mo.vstack([
    mo.md("### Per sampler: bugs killed, at its own size and at 3 boxes"),
    mo.ui.table([{
        "sampler": SHORT[s],
        "killed": percent(killed(s)),
        "detected": percent(detected(s)),
        "killed at 3 boxes": percent(killed(s, "matched 3")),
        **shrinking(s),
        **({"boundaries glued": percent(glue(s))}
           if glue(s) is not None else {}),
    } for s in samplers], selection=None, show_column_summaries=False)
    if mutant_rows else mo.md("not run yet"),
    mo.md("""
*Killed* is the mean kill rate over the mutants, *detected* counts the
crashes of the sampler too, which a run of the matrix would report without a
counterexample to the law; *shrunk terms* counts the
boxes, structural boxes and layers of the shrunk arguments, *shrinking
calls* the evaluations of the law Hypothesis spent shrinking them, both
medians over kills. *Boundaries glued* is, for the samplers with a grammar,
the share of the boundaries the laws asked for that it does not derive.
"""),
])
```

```python {.marimo hide_code="true"}
def listed(xs):
    return ", ".join(xs) or "none"


def always(mutant):
    return [SHORT[s] for s in samplers if rate(mutant, s) == 1]


def never(mutant):
    return [SHORT[s] for s in samplers if rate(mutant, s) == 0]


def crashing():
    return sorted({SHORT[r["sampler"]] for r in mutant_rows if r["crash"]})


best = max(samplers, key=killed) if samplers else None
mo.md(f"""
## Planted bugs: what we read

- **Two boxes in a row** (`layer_overlap`) are killed every time by
  {listed(always('layer_overlap'))}: the commonest shape there is.
- **A permutation that is not an involution** (`permutation_convention`) is
  never killed by {listed(never('permutation_convention'))}, which never
  draw a cycle of three wires: their swaps are transpositions.
- **A layer of two boxes** (`layer_offsets`) is killed every time by
  {listed(always('layer_offsets'))} and never by
  {listed(never('layer_offsets'))}.
- **A trace on the left** (`left_trace`) is killed every time by
  {listed(always('left_trace'))}: the law of yanking builds a left trace
  itself, whatever the sampler draws.
- **The identity printed as the empty string** (`identity_string`) is
  killed every time by {listed(always('identity_string'))}; counting a
  failure only when the code without the mutant passes no longer lets a law
  that already fails hide it.
- **A bug in the code a sampler runs crashes the sampler**, under
  {listed(crashing())}: reading a hypergraph back is part of drawing, so the
  mutant breaks the sampler before any law sees a term.
- **The portfolio** kills {percent(killed('portfolio'))} of the mutants on
  average and detects {percent(detected('portfolio'))}, the best single
  sampler {SHORT.get(best, best)} kills {percent(killed(best)) if best else ''}:
  a third of its draws from 3a is enough to inherit both its cycles of wires
  and its crashes.
- **The grammar is the weakest on the layer bugs**: 2c kills
  {percent(killed('syntactic_grammatical'))} of the mutants and 2bc
  {percent(killed('syntactic_grammatical_admissible'))}, since most of their
  draws are one or two boxes, and matching sizes helps little, since their
  tail is what Hypothesis cuts.
- **A first attempt at interlocked traces was an equivalent mutant**:
  feeding back a trace of two wires crossed changes nothing, since a trace
  of a symmetric diagram reaches the hypergraph one wire at a time.
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
  one it cannot is known before any draw. The grammars find the most
  distinct tensors there: {semantic_row('syntactic_grammatical')['tensors']}
  under 2c and {semantic_row('syntactic_grammatical_admissible')['tensors']}
  under 2bc, against at most {max((r['tensors'] for r in semantic
  if r['boundary'] == 'fixed' and not r['sampler'].startswith(
  'syntactic_grammatical')), default=0)} for the others.
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
| Critical sampling for `explore`? | decided: no, `explore` samples shrinkable terms at a finite size; critical sampling only pays drawn from a seed, which does not shrink, so it is left for later | decided |
| A combinatorial class for each doctrine? | symmetric: matchings; markov: functions; compact: Brauer pairings, all implemented in 3a; braided (braid words) and pivotal (Temperley–Lieb) have no structural sampler yet, frobenius draws spiders through markov's | high |
| Semantic categories? | only the grammar respects a fixed signature without rejection | high |
| Normal or non-normal forms? | both: cycles of wires need the structural samplers, which draw normal forms, but those crash on bugs in the code they run themselves and hide bugs behind laws they break; a mixture per law covers both | medium |
| Pairs of equal diagrams? | 3p draws a rewritten normal form, which the laws already compare with its quotient; a law over pairs is a next step | low |

<!---->

## 10. What to do next

1. The `--full` run, then choose the default sampler of each doctrine from
   these numbers: the portfolio of 2c, 3a and 3b is the candidate to beat.
2. Regression examples: `Axiom.examples`, run once per cell with
   `@example`, for every counterexample found so far.
3. Structural samplers below monoidal: braid words for braided and
   balanced diagrams, Temperley–Lieb for pivotal ones, and the tuning of 3a.
4. Critical sampling for `explore`, drawn from a seed, once a shrinkable
   form of it exists.
