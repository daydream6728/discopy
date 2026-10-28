"""True isomorphism classes against the benchmark's canonical-form classes."""
import re, sys, warnings
warnings.simplefilter("ignore")
from collections import Counter
from hypothesis import HealthCheck, Phase, given, settings, strategies as st
from networkx import is_isomorphic, weisfeiler_lehman_graph_hash
from discopy import frobenius, compact, markov, plumbing

N = 300
SETTINGS = settings(max_examples=N, database=None, deadline=None,
                    phases=[Phase.generate], derandomize=True,
                    suppress_health_check=list(HealthCheck))

def anonymous(graph):
    """ The hypergraph with every generator named f, as a networkx graph. """
    g = graph.to_graph()
    for node, data in g.nodes(data=True):
        for key, value in list(data.items()):
            data[key] = re.sub(r"f_[0-9a-f]{32}", "f", repr(value))
    return g

def classes(diagrams):
    """ The number of isomorphism classes, exactly, by WL hash then VF2. """
    buckets, count = {}, 0
    for d in diagrams:
        g = anonymous(d.to_hypergraph())
        key = (repr(d.dom), repr(d.cod), weisfeiler_lehman_graph_hash(g, node_attr="box"))
        reps = buckets.setdefault(key, [])
        if not any(is_isomorphic(g, h, node_match=lambda a, b: a == b) for h in reps):
            reps.append(g)
            count += 1
    return count

def metric(d):
    graph = d.to_hypergraph()
    canonical = graph.boundary_rooted_canonical()
    shape = re.sub(r"f_[0-9a-f]{32}", "f", str(d))
    return shape if canonical is None else re.sub(
        r"f_[0-9a-f]{32}", "f", repr((canonical.dom, canonical.cod, canonical.boxes, canonical.wires)))

def draw(strategy):
    out = []
    @SETTINGS
    @given(st.data())
    def run(data):
        out.append(data.draw(strategy))
    run()
    return out

for module in (frobenius, markov, compact):
    x = module.Ty('x')
    D = module.Diagram
    gens = {"derivations+graphs": D.strategy(dom=x, cod=x),
            "plumbing": plumbing.strategy(D, x, x)}
    for name, strategy in gens.items():
        ds = draw(strategy)
        graphs = [d.to_hypergraph() for d in ds]
        fast = sum(g.is_fast_eligible for g in graphs)
        mono = sum(g.is_monogamous for g in graphs)
        print(module.__name__, name, "draws", len(ds),
              "metric classes", len(set(map(metric, ds))),
              "true classes", classes(ds),
              "monogamous", mono, "fast-eligible", fast, flush=True)
