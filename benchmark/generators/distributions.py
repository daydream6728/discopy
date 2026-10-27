"""
Compare the generators of free diagrams, run from the root of a checkout.

Usage: python distributions.py <generator> <out.jsonl> [samples|bugs], or
run.sh for several jobs against a checkout.

Generators: search, quotient, mixed (the default of #1, on its base
commit), boltzmann, boltzmann_mixed (the default of this branch).

``samples`` draws 300 diagrams per category and boundary through Hypothesis
and records their size, structure and shape; ``bugs`` searches each law
declared broken on a free category for an input where its underlying
equation fails, up to 100 examples, and records how many it took.
"""

import importlib
import json
import re
import sys
import time
import warnings
from collections import Counter

warnings.simplefilter("ignore")

from hypothesis import HealthCheck, Phase, find, given, settings
from hypothesis import strategies as st
from hypothesis.errors import NoSuchExample, UnsatisfiedAssumption

from discopy import symmetric
from discopy.axioms import AxiomFailure, FUEL, Testable
from discopy.cat import Arrow, FreeCategory

GENERATOR, OUT = sys.argv[1], sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else "samples"

MODULES = ["monoidal", "braided", "rigid", "pivotal", "symmetric", "feedback",
           "compact", "markov", "closed", "frobenius"]
N = int(__import__("os").environ.get("N", 300))
SETTINGS = settings(
    max_examples=N, database=None, deadline=None, phases=[Phase.generate],
    suppress_health_check=list(HealthCheck), derandomize=True)


def patch():
    """ Make every free diagram category draw from one generator only. """
    original = symmetric.Diagram.strategy.__func__
    arrow = Arrow.strategy.__func__

    def only(cls, *, dom=None, cod=None, fuel=FUEL, within=None):
        if GENERATOR == "search":
            return cls.search(dom=dom, cod=cod, fuel=fuel, within=within)
        if GENERATOR == "quotient" and within is None\
                and hasattr(cls, "quotient_strategy"):
            return cls.quotient_strategy(dom=dom, cod=cod, fuel=fuel)
        if GENERATOR == "quotient":
            return cls.search(dom=dom, cod=cod, fuel=fuel, within=within)
        if GENERATOR == "boltzmann":
            return arrow(cls, dom=dom, cod=cod, fuel=fuel, within=within)
        return original(cls, dom=dom, cod=cod, fuel=fuel, within=within)

    if GENERATOR in ("search", "quotient", "boltzmann"):
        symmetric.Diagram.strategy = classmethod(only)
        if GENERATOR == "search":
            Arrow.strategy = classmethod(only)


def flatten(diagram):
    """ The boxes of a diagram, and those inside its bubbles. """
    for box in diagram.boxes:
        yield box
        for arg in getattr(box, "args", ()) or ():
            if isinstance(arg, Arrow) and arg is not box:
                yield from flatten(arg)


def metrics(module, diagram, seconds):
    boxes = list(flatten(diagram))
    generators = [b for b in boxes if re.fullmatch(r"f_[0-9a-f]{32}", b.name)]
    kinds = Counter(type(b).__name__ for b in boxes
                    if b not in generators and type(b).__name__ != "Box")
    shape = re.sub(r"f_[0-9a-f]{32}", "f", str(diagram))
    try:
        graph = diagram.to_hypergraph()
        canonical = graph.boundary_rooted_canonical()
        quotient = shape if canonical is None else re.sub(
            r"f_[0-9a-f]{32}", "f", repr((canonical.dom, canonical.cod,
                                          canonical.boxes, canonical.wires)))
    except Exception:  # pylint: disable=broad-except
        quotient = None
    return dict(
        module=module, dom=len(diagram.dom), cod=len(diagram.cod),
        generators=len(generators), structure=dict(kinds),
        layers=len(diagram), shape=shape, quotient=quotient, seconds=seconds)


def samples(out):
    for name in MODULES:
        module = importlib.import_module(f"discopy.{name}")
        x = module.Ty("x")
        for boundary, (dom, cod) in {"x->x": (x, x),
                                     "free": (None, None)}.items():
            rows, last = [], [time.time()]

            @SETTINGS
            @given(st.data())
            def draw(data):
                diagram = data.draw(module.Diagram.strategy(dom=dom, cod=cod))
                now = time.time()
                rows.append(metrics(name, diagram, now - last[0]))
                last[0] = now

            try:
                draw()
            except Exception as error:  # pylint: disable=broad-except
                print(name, boundary, "ERROR", repr(error)[:200], flush=True)
            for row in rows:
                out.write(json.dumps(dict(row, boundary=boundary)) + "\n")
            print(name, boundary, len(rows), flush=True)


def bugs(out):
    cells = [law for law in Testable.matrix()
             if law.broken and isinstance(law.category, type)
             and issubclass(law.category, FreeCategory)
             and law.category.__module__.removeprefix("discopy.")
             in MODULES + ["balanced", "ribbon", "comarkov", "biclosed"]]
    class Found(Exception):
        """ The first counterexample, which stops the search. """

    def searcher(law, original, calls):
        @settings(max_examples=100, database=None, deadline=None,
                  derandomize=True, phases=[Phase.generate],
                  suppress_health_check=list(HealthCheck))
        @given(law.strategy())
        def search(arguments):
            calls[0] += 1
            try:
                verdict = original(law.category, **arguments)
            except (UnsatisfiedAssumption, AxiomFailure):
                return
            except Exception:  # pylint: disable=broad-except
                raise Found()
            if verdict is not NotImplemented and not verdict:
                raise Found()
        return search

    for law in cells:
        original = law.function.__wrapped__
        calls = [0]
        search = searcher(law, original, calls)

        start = time.time()
        try:
            search()
            found = False
        except Found:
            found = True
        except Exception as error:  # pylint: disable=broad-except
            found = "Found" in repr(error)
            if not found:
                print(repr(law), "ERROR", repr(error)[:160], flush=True)
        out.write(json.dumps(dict(
            law=repr(law), found=found, calls=calls[0],
            seconds=time.time() - start)) + "\n")
        out.flush()


patch()
with open(OUT, "w") as stream:
    (samples if MODE == "samples" else bugs)(stream)
