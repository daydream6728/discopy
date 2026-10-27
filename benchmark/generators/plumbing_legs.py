import random, statistics
from discopy.plumbing import Plumbing, Sampler
for kind in ("cospan", "function"):
    for legs in (1., .5, .3, .1, 0.):
        s = Sampler(Plumbing(kind, q=.5, legs=legs, feedback=.3), loops=0).exactly(4)
        rng = random.Random(0); rows = []
        for _ in range(3000):
            w = s.walk(rng, 1, 1); sizes = [len(x) for x in w.wires]
            rows.append((sizes.count(1), sum(z > 2 for z in sizes), sum(abs(z-2) for z in sizes), len(sizes), w.crossings))
        m = [round(statistics.mean(r[i] for r in rows), 2) for i in range(5)]
        print(kind, legs, dict(zip(["one-legged", "spiders", "energy", "wires", "crossings"], m)))
