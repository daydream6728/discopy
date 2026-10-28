import sys, warnings
warnings.simplefilter("ignore")
sys.argv = ["x"]
import hypothesis.strategies
from hypothesis import strategies as st
original = st.randoms
seeds = []
def recording(**kw):
    return original(**kw).map(lambda r: (seeds.append(r.getstate()[1][:4]), r)[1])
hypothesis.strategies.randoms = recording
import importlib.util
spec = importlib.util.spec_from_file_location("c", "/tmp/claude-0/-home-claude/e9a98549-3a18-5df4-81e1-d5a5b7a24cc1/scratchpad/frob/classes.py")
src = open(spec.origin).read().split("for module in (frobenius")[0]
exec(src)
from discopy import frobenius, compact, markov
for module in (frobenius, markov, compact):
    x = module.Ty('x'); seeds.clear()
    ds = draw(module.Diagram.strategy(dom=x, cod=x))
    print(module.__name__, "derivations: seeds", len(set(seeds)), "of", len(seeds), "classes", classes(ds), flush=True)
