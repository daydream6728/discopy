import random, re, sys, warnings
warnings.simplefilter("ignore")
sys.path.insert(0, "/tmp/claude-0/-home-claude/e9a98549-3a18-5df4-81e1-d5a5b7a24cc1/scratchpad/frob")
from collections import Counter
from hypothesis import strategies as st
from classes import classes, draw
from discopy import frobenius, plumbing
from discopy.hypergraph import Hypergraph

seeds, ks = [], []
original = st.randoms
def recording(**kw):
    return original(**kw).map(lambda r: (seeds.append(r.getstate()[1][:4]), r)[1])
plumbing_st = st.randoms
import hypothesis.strategies
hypothesis.strategies.randoms = recording
x = frobenius.Ty('x'); D = frobenius.Diagram
ds = draw(plumbing.strategy(D, x, x))
print("hypothesis: draws", len(ds), "distinct seeds", len(set(seeds)), "of", len(seeds),
      "true classes", classes(ds))
hypothesis.strategies.randoms = original

sampler = plumbing.sampler(plumbing.Plumbing("cospan", q=.5, feedback=.3, legs=.3, acyclic=False), 6)
rng = random.Random(1)
palette = (x, frobenius.Ty('a'))
out = []
from discopy.plumbing import colour
while len(out) < 300:
    k = rng.randint(0, 6)
    shapes, wires = sampler.exactly(k).sample(rng, 1, 1)
    args = colour(D, shapes, wires, (x, x), (1, 1), palette, rng)
    if args is None: continue
    dom, cod, types, wiring, spiders = args
    boxes = tuple(D.box_factory(f"f_{rng.getrandbits(128):032x}", a, b) for a, b in types)
    out.append(Hypergraph[D](dom, cod, boxes, wiring, spiders).to_diagram())
print("fresh seeds: draws", len(out), "true classes", classes(out))
