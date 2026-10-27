import random, statistics, sys, warnings
warnings.simplefilter("ignore")
from discopy import compact, symmetric
from discopy.hypergraph import Hypergraph
from discopy.plumbing import Plumbing, Sampler, colour

def diagrams(module, kind, q, k, n, acyclic=False, feedback=1.):
    D, x = module.Diagram, module.Ty('x')
    s = Sampler(Plumbing(kind, q=q, acyclic=acyclic, feedback=feedback), loops=0).exactly(k)
    rng = random.Random(0); out = []
    while len(out) < n:
        walk = s.walk(rng, 1, 1)
        args = colour(D, walk.shapes, walk.wires, (x, x), (1, 1), (x,), rng)
        dom, cod, types, wiring, spiders = args
        boxes = tuple(D.box_factory(f"f{i}", a, b) for i, (a, b) in enumerate(types))
        out.append((walk.crossings, Hypergraph[D](dom, cod, boxes, wiring, spiders).to_diagram()))
    return out

for module, kind, acyclic in ((compact, "matching", False), (symmetric, "bijection", True), (symmetric, "bijection", False)):
    for q in (0., .5, 1.):
        rows = []
        for crossings, d in diagrams(module, kind, q, 3, 200, acyclic):
            cmap = d.to_map()
            genus = sum(c.genus for c in cmap.connected_components)
            rows.append((crossings, genus, len(cmap.connected_components)))
        print(module.__name__, kind, "acyclic" if acyclic else "", q,
              "crossings %.2f" % statistics.mean(r[0] for r in rows),
              "genus %.2f" % statistics.mean(r[1] for r in rows),
              "planar %.0f%%" % (100 * statistics.mean(r[1] == 0 for r in rows)),
              "components %.2f" % statistics.mean(r[2] for r in rows), flush=True)
