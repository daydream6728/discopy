import warnings; warnings.simplefilter("ignore")
src = open("/tmp/claude-0/-home-claude/e9a98549-3a18-5df4-81e1-d5a5b7a24cc1/scratchpad/frob/classes.py").read().split("for module in (frobenius")[0]
exec(src)
from discopy import frobenius, markov, compact, symmetric, plumbing
for module in (frobenius, markov, compact, symmetric):
    x = module.Ty('x'); D = module.Diagram
    ds = draw(plumbing.strategy(D, x, x))
    print(module.__name__, "plumbing, seeded by every draw: classes", classes(ds), "of", len(ds), flush=True)
