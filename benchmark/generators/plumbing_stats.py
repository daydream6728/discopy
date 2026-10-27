"""Plumbing statistics against q, and growth of the weighted counts."""
import json, random, statistics, sys
from discopy.plumbing import Plumbing, Sampler

KINDS = [("bijection", False), ("bijection", True), ("matching", False),
         ("function", False), ("cospan", False)]
QS = [0., .25, .5, .75, 1.]
out = {"stats": [], "growth": []}

def describe(kind, walk, dom):
    points = [True] * dom + [p for m, n in walk.shapes
                             for p in m * [False] + n * [True]] + [False]
    wires = [w for w in walk.wires if w]
    first_consumer = sum(1 for w in wires if not points[w[0]])
    same_kind = sum(1 for w in wires if len(w) == 2 and points[w[0]] == points[w[1]])
    sizes = [len(w) for w in wires]
    return dict(crossings=walk.crossings, feedback=first_consumer,
                cups_caps=same_kind, wires=len(wires),
                singletons=sizes.count(1), big=sum(s > 2 for s in sizes))

for kind, acyclic in KINDS:
    for q in QS:
        sampler = Sampler(Plumbing(kind, q=q, acyclic=acyclic, feedback=.3),
                          loops=0).exactly(4)
        rng = random.Random(0)
        rows = [describe(kind, sampler.walk(rng, 1, 1), 1) for _ in range(3000)]
        mean = {k: round(statistics.mean(r[k] for r in rows), 2) for k in rows[0]}
        out["stats"].append(dict(kind=kind, acyclic=acyclic, q=q, **mean))
        print(kind, acyclic, q, mean, flush=True)
    for q in (.5, 1.):
        c = Sampler(Plumbing(kind, q=q, acyclic=acyclic, feedback=1.),
                    max_boxes=9).coefficients(1, 1)
        ratios = [round((k + 1) * c[k + 1] / c[k], 1) for k in range(len(c) - 1)]
        out["growth"].append(dict(kind=kind, acyclic=acyclic, q=q, ratios=ratios))
        print("  growth", q, ratios, flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
