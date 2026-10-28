import warnings; warnings.simplefilter("ignore")
from collections import Counter
import discopy.plumbing as P
src = open("/tmp/claude-0/-home-claude/e9a98549-3a18-5df4-81e1-d5a5b7a24cc1/scratchpad/frob/classes.py").read().split("for module in (frobenius")[0]
exec(src)
from discopy import frobenius
seen = []
Original = P.Random
class Logged(Original):
    def __init__(self, x=None):
        seen.append(x); super().__init__(x)
P.Random = Logged
x = frobenius.Ty('x')
ds = draw(P.strategy(frobenius.Diagram, x, x))
seeds = Counter(s.split(",")[0] for s in seen); ks = Counter(s.split(",")[1] for s in seen)
print("examples", len(ds), "Random() calls", len(seen), "distinct inputs", len(set(seen)), "distinct seeds", len(seeds))
print("k", sorted(ks.items())); print("top seeds", seeds.most_common(5))
