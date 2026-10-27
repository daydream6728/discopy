"""
Compare the hypergraphs Hypergraph[C].strategy draws with those a Boltzmann
diagram of C reads as, on the branch.
"""

import importlib
import json
import statistics
import sys
import warnings
from collections import Counter

warnings.simplefilter("ignore")

from hypothesis import HealthCheck, Phase, given, settings
from hypothesis import strategies as st

from discopy.cat import Arrow
from discopy.hypergraph import Hypergraph

N = 300
SETTINGS = settings(
    max_examples=N, database=None, deadline=None, phases=[Phase.generate],
    suppress_health_check=list(HealthCheck), derandomize=True)


def features(graph):
    legs = Counter()
    dom, boxes, cod = graph.wires
    for spider in dom + cod:
        legs[spider] += 1
    for ins, outs in boxes:
        for spider in ins + outs:
            legs[spider] += 1
    degrees = [legs[i] for i in range(graph.n_spiders)]
    return dict(
        boxes=len(graph.boxes), spiders=graph.n_spiders,
        loops=sum(1 for d in degrees if d == 0),
        fanout=max(degrees, default=0),
        branching=sum(1 for d in degrees if d > 2),
        cyclic=not graph.is_acyclic if hasattr(graph, "is_acyclic") else None,
        connected=graph.is_boundary_connected
        if hasattr(graph, "is_boundary_connected") else None)


def collect(strategy):
    rows = []

    @SETTINGS
    @given(strategy)
    def draw(graph):
        rows.append(features(graph))

    draw()
    return rows


def summary(rows):
    return {key: statistics.mean(float(r[key] or 0) for r in rows)
            for key in rows[0]} | {"n": len(rows)}


out = {}
for name in sys.argv[1:]:
    module = importlib.import_module(f"discopy.{name}")
    H = Hypergraph[module.Diagram]
    x = module.Ty("x")
    out[name] = {
        "sampler": summary(collect(H.strategy(dom=x, cod=x))),
        "boltzmann": summary(collect(
            Arrow.strategy.__func__(module.Diagram, dom=x, cod=x).map(
                lambda d: d.to_hypergraph()))),
    }
    print(name, json.dumps(out[name]), flush=True)
