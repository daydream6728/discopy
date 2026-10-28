import random, sys, warnings
warnings.simplefilter("ignore")
import hypothesis.strategies
from hypothesis import strategies as st
original = st.randoms
src = open("/tmp/claude-0/-home-claude/e9a98549-3a18-5df4-81e1-d5a5b7a24cc1/scratchpad/frob/classes.py").read().split("for module in (frobenius")[0]
exec(src)
from discopy import frobenius, markov, compact, plumbing

seeds = []
VARIANTS = {
    "randoms(true)": lambda **kw: original(use_true_random=True),
    "binary seed": lambda **kw: st.binary(min_size=16, max_size=16).map(random.Random),
    "randoms(false)": lambda **kw: original(use_true_random=False),
}
for module in (frobenius, compact):
    x = module.Ty('x'); D = module.Diagram
    for name, variant in VARIANTS.items():
        seeds.clear()
        hypothesis.strategies.randoms = lambda variant=variant, **kw: variant(**kw).map(
            lambda r: (seeds.append(repr(r.getstate())[:80] if hasattr(r, 'getstate') else id(r)), r)[1])
        plumbing.sampler.cache_clear()
        ds = draw(plumbing.strategy(D, x, x))
        print(module.__name__, name, "seeds", len(set(seeds)), "of", len(seeds),
              "classes", classes(ds), "boxes %.2f" % (sum(len(d.to_hypergraph().boxes) for d in ds) / len(ds)), flush=True)
hypothesis.strategies.randoms = original
