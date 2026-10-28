""" Summarise the samples and bug-finding runs of dist.py into JSON. """

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXP = Path(sys.argv[1])
GENERATORS = ["search", "quotient", "mixed", "boltzmann_free", "boltzmann_topdown", "boltzmann", "boltzmann_mixed", "plumbing", "boltzmann_plumbing", "plumbing_flat", "boltzmann_plumbing_flat", "plumbing_legs", "boltzmann_plumbing_legs"]


def load(kind, generator):
    path = EXP / f"{kind}-{generator}.jsonl"
    return [json.loads(line) for line in path.open()] if path.exists() else []


def summary(rows):
    sizes = [r["generators"] for r in rows]
    structure = Counter(k for r in rows for k in r["structure"])
    return dict(
        n=len(rows),
        mean_boxes=statistics.mean(sizes),
        median_boxes=statistics.median(sizes),
        p90_boxes=sorted(sizes)[int(.9 * len(sizes)) - 1],
        max_boxes=max(sizes),
        identity=sum(1 for r in rows if not r["generators"]
                     and not r["structure"]) / len(rows),
        one_box=sum(1 for r in rows if r["generators"] == 1
                    and not r["structure"]) / len(rows),
        mean_layers=statistics.mean(r["layers"] for r in rows),
        mean_wires=statistics.mean(r["dom"] + r["cod"] for r in rows),
        structured=sum(1 for r in rows if r["structure"]) / len(rows),
        kinds={k: v / len(rows) for k, v in structure.most_common()},
        shapes=len({r["shape"] for r in rows}) / len(rows),
        classes=len({r["quotient"] or r["shape"] for r in rows}) / len(rows),
        ms=1000 * statistics.mean(r["seconds"] for r in rows),
        histogram=Counter(min(s, 12) for s in sizes))


samples = {}
for generator in GENERATORS:
    groups = defaultdict(list)
    for row in load("samples", generator):
        groups[(row["module"], row["boundary"])].append(row)
    samples[generator] = {
        f"{m}|{b}": summary(rows) for (m, b), rows in groups.items()}

bugs = {}
for generator in GENERATORS:
    rows = load("bugs", generator)
    if rows:
        bugs[generator] = {r["law"]: r for r in rows}

json.dump(dict(samples=samples, bugs=bugs),
          (EXP / "summary.json").open("w"), indent=1)

for generator, table in samples.items():
    if not table:
        continue
    print(f"\n== {generator}")
    print(f"{'module|boundary':26s} {'boxes':>6s} {'p90':>4s} {'id%':>5s}"
          f" {'1box%':>6s} {'struct%':>7s} {'shapes':>6s} {'classes':>7s}"
          f" {'ms':>6s}")
    for key, s in table.items():
        print(f"{key:26s} {s['mean_boxes']:6.2f} {s['p90_boxes']:4d}"
              f" {100 * s['identity']:5.1f} {100 * s['one_box']:6.1f}"
              f" {100 * s['structured']:7.1f} {s['shapes']:6.2f}"
              f" {s['classes']:7.2f} {s['ms']:6.1f}")

for generator, table in bugs.items():
    found = [r for r in table.values() if r["found"]]
    print(f"\n{generator}: found {len(found)}/{len(table)} broken laws, "
          f"median {statistics.median([r['calls'] for r in found] or [0])}"
          f" examples, {sum(r['seconds'] for r in table.values()):.0f}s")
