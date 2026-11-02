"""
Experiments comparing the samplers of string diagrams, see ``analysis.md``.

Each experiment writes its raw results to ``sampling/results/<name>.json``,
which ``analysis.md`` and ``presentation.md`` read: neither runs an
experiment.

    uv run --with cvxpy python sampling/experiments.py --quick
    uv run --with cvxpy python sampling/experiments.py --quick boltzmann

``--quick`` is the budget the notebooks are regenerated with, ``--full``
about three times it, ``--smoke`` a few examples of everything, to check
that it runs, written to ``results/smoke``. A full run is split in shards,
one cloud session each, e.g.

    uv run --with cvxpy python sampling/experiments.py --full \\
        calibration throughput --out throughput
    uv run python sampling/experiments.py --merge throughput mutants matrix

``--doctrines monoidal,symmetric`` restricts any experiment to some
doctrines, ``--reuse-calibration`` copies ``results/calibration.json``.
"""

import argparse
import concurrent.futures
import itertools
import json
import math
import os
import pathlib
import random
import re
import subprocess
import sys
import statistics
import time
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from dataclasses import asdict, dataclass

import networkx as nx
import numpy as np
from hypothesis import HealthCheck, Phase, find, given, settings
from hypothesis import seed as hypothesis_seed
from hypothesis import strategies as st
from hypothesis.errors import NoSuchExample, Unsatisfiable
from hypothesis.internal.observability import with_observability_callback

from discopy import (
    balanced, biclosed, braided, cat, closed, comarkov, compact, feedback,
    frobenius, markov, monoidal, pivotal, ribbon, rigid, spacial, symmetric,
    tensor)
from discopy.abc import SymmetricCategory
from discopy.boltzmann import Grammar
from discopy.testable import Testable
from discopy.utils import factory_name

HERE = pathlib.Path(__file__).parent
RESULTS = HERE / "results"
OUT = RESULTS
""" Where the experiments write, ``results/<shard>`` for a shard. """

SELECTED = None
""" The doctrines to run on, all of them if ``None``, see ``--doctrines``. """

WORKERS = int(os.environ.get("SAMPLING_WORKERS", 0)) or None
"""
The processes of a parallel experiment, ``SAMPLING_WORKERS`` or one for
each core.
"""
sys.path.insert(0, str(HERE))

from mutants import MUTANTS  # noqa: E402  pylint: disable=wrong-import-position

SAMPLERS = (
    "representational_baseline",
    "representational_goal_directed",
    "syntactic_baseline",
    "syntactic_admissible",
    "syntactic_grammatical",
    "structural_typed",
    "structural_implicit",
    "structural_perturbed",
    "syntactic_grammatical_admissible",
    "portfolio",
)
""" The samplers, by the name of their method ``strategy_<sampler>``. """

ALPHABET = ("a", "b")
"""
The atoms every sampler draws its types from in the experiments run here,
those of the grammar of :meth:`strategy_syntactic_grammatical`, so that the
samplers compete on the same types; the matrix runs on the default atoms.
"""

MATCHED = (3., 6.)
""" The mean numbers of boxes the samplers are calibrated to. """

SEEDS = {"smoke": 1, "quick": 3, "full": 5}
""" The seeds each mutant is searched for under each sampler. """

DOCTRINES = {
    "cat": cat,
    "monoidal": monoidal,
    "spacial": spacial,
    "braided": braided,
    "balanced": balanced,
    "ribbon": ribbon,
    "rigid": rigid,
    "pivotal": pivotal,
    "symmetric": symmetric,
    "feedback": feedback,
    "markov": markov,
    "comarkov": comarkov,
    "frobenius": frobenius,
    "compact": compact,
    "closed": closed,
    "biclosed": biclosed,
}
"""
Every level of the hierarchy of free categories, by module: the arrows of
:mod:`discopy.cat`, then the diagrams of each other module. A traced
category has no diagrams of its own: its traces are those of
:mod:`discopy.feedback` and below.
"""

BUDGETS = {
    "throughput": {"smoke": 10, "quick": 200, "full": 300},
    "boltzmann": {"smoke": 10, "quick": 300, "full": 1000},
    "mutants": {"smoke": 3, "quick": 30, "full": 100},
    "semantic": {"smoke": 10, "quick": 200},
    "uniforms": {"smoke": 100, "quick": 2000},
    "calibration": {"smoke": 10, "quick": 100, "full": 50},
}
"""
Examples per cell of each experiment, by mode: ``smoke`` only checks that
everything runs, and writes to ``results/smoke`` instead.
"""

PROFILES = {"smoke": "pr", "quick": "pr", "full": "pr"}
"""
The Hypothesis profile the property matrix is run under: ``pr`` for a full
run too, since the matrix only shows that no law fails under any sampler,
and finding bugs is what the planted ones measure.
"""

QUICK_ONLY = ("convex", "semantic", "uniforms")
""" The experiments whose quick results are conclusive, with no full run. """

ORIGINAL = ("monoidal", "symmetric", "markov", "compact")
"""
The doctrines the Boltzmann experiment runs at its full budget, one for
each class of plumbing; the others run at the quick budget.
"""

FRESH = re.compile(r"f_[0-9a-f]{32}")
""" The name of a fresh box, see :meth:`discopy.cat.Box.strategy`. """


def diagram_class(doctrine):
    """ The free category of a doctrine: arrows for cat, else diagrams. """
    module = DOCTRINES[doctrine]
    return module.Arrow if module is cat else module.Diagram


def implemented(doctrine):
    """ The samplers a doctrine of this round implements. """
    diagram = diagram_class(doctrine)
    return [s for s in SAMPLERS if hasattr(diagram, f"strategy_{s}")]


def doctrines():
    """ The doctrines selected, every one by default, see :data:`DOCTRINES`. """
    return [d for d in DOCTRINES if SELECTED is None or d in SELECTED]


def parallel(function, tasks):
    """
    Map ``function`` over ``tasks`` in a pool of processes, one task each,
    and concatenate the rows they return, in the order of the tasks.
    """
    rows = []
    with concurrent.futures.ProcessPoolExecutor(WORKERS) as pool:
        for found in pool.map(function, tasks):
            rows += found
    return rows


@contextmanager
def sampler(diagram, name):
    """ Sample the diagrams of a class by the given sampler, in a block. """
    old = diagram.__dict__.get("default_strategy")
    diagram.default_strategy = name
    try:
        yield
    finally:
        if old is None:
            del diagram.default_strategy
        else:
            diagram.default_strategy = old


@contextmanager
def alphabet(atoms=ALPHABET):
    """ Draw the types of the free categories from ``atoms``, in a block. """
    old = cat.GENERATORS
    cat.GENERATORS = atoms
    try:
        yield
    finally:
        cat.GENERATORS = old


@contextmanager
def calibrated(diagram, name, params):
    """
    Sample the diagrams of a class by the given sampler with the given
    default parameters, e.g. ``{"fuel": 2}``, in a block: a caller that
    passes its own, as a rule passes its fuel down, overrides them.
    """
    def strategy(cls, **given):
        return getattr(cls, f"strategy_{name}")(**params | given)

    diagram.strategy_calibrated = classmethod(strategy)
    try:
        with sampler(diagram, "calibrated"):
            yield
    finally:
        del diagram.strategy_calibrated


def knob(name):
    """ The parameter that sets the size of a sampler, and its values. """
    if name.startswith("syntactic_grammatical"):
        return "size", (1., 2., 4., 8., 16., 32., 64.)
    return "fuel", tuple(range(0, 9))


@dataclass
class Size:
    """ The sizes of a diagram, see ``analysis.md``. """
    boxes: int
    layers: int
    width: int
    crossings: int
    structural: int

    @staticmethod
    def of(diagram):
        """
        Count the generators, i.e. the boxes of the signature, the layers,
        the widest
        boundary, the crossings, i.e. the inversions of each
        permutation, and the other structural boxes, e.g. copies, cups or
        traces.
        """
        boxes = list(flatten(diagram))
        perms = [box for box in boxes if hasattr(box, "perm")]
        generators = [
            box for box in boxes if type(box) is type(diagram).box_factory]
        return Size(
            boxes=len(generators),
            layers=len(diagram),
            width=max([width(diagram.dom), width(diagram.cod)] + [
                width(layer.dom) for layer in diagram.inside]),
            crossings=sum(inversions(list(box.perm)) for box in perms),
            structural=len(boxes) - len(generators) - len(perms))


def width(obj):
    """ The number of wires of a type, one for an object of a category. """
    return len(obj) if hasattr(obj, "__len__") else 1


def flatten(diagram):
    """ The boxes of a diagram, those inside a trace or a bubble included. """
    for box in getattr(diagram, "boxes", diagram.inside):
        if hasattr(box, "arg"):
            yield box
            yield from flatten(box.arg)
        else:
            yield box


def inversions(xs):
    """ The number of pairs out of order, i.e. of crossings. """
    return sum(x > y for i, x in enumerate(xs) for y in xs[i + 1:])


def shape(diagram):
    """ A diagram up to the names of its fresh boxes. """
    return FRESH.sub("f", repr(diagram))


STEPS = 500
""" The rewrites a planar normal form is computed with, at most. """


def coherent_shape(diagram):
    """
    A diagram up to the names of its fresh boxes and up to coherence: the
    Weisfeiler-Lehman hash of its hypergraph for a symmetric category,
    which isomorphic hypergraphs share, else its planar normal form, when
    it is boundary-connected and has one, after at most :data:`STEPS`
    rewrites: a diagram with several scalars takes exponentially many to
    be found to have none, see ``retrospective.md``.
    """
    if not isinstance(diagram, SymmetricCategory):
        def capped(term, **params):
            return itertools.islice(type(term).normalize(term, **params), STEPS)
        try:
            return shape(diagram.normal_form(normalize=capped))
        except (AttributeError, NotImplementedError):
            return shape(diagram)
    graph = diagram.to_hypergraph().to_graph()
    for node, data in graph.nodes(data=True):
        kind = repr(node).split("'")[1]
        box = data.get("box")
        data["label"] = ":".join(map(str, (
            kind, data.get("obj", ""),
            data.get("i", "") if kind in ("input", "output") else "",
            data.get("j", ""),
            FRESH.sub("f", f"{type(box).__name__}{box.dom}{box.cod}")
            if kind == "box" else "")))
    return nx.weisfeiler_lehman_graph_hash(graph, node_attr="label")


def sample(strategy, budget, seed=None, warmup=True):
    """
    Run ``strategy`` for ``budget`` examples in the generate phase only,
    from a ``seed`` if given so that the draws are reproducible, after a few
    examples drawn and thrown away if ``warmup``, so that what the strategy
    computes once, e.g. a grammar, is not timed, and return each valid
    diagram with the time it took and the count of test cases Hypothesis
    gave up on, by reason: ``rejected`` by the sampler, a failed ``assume``
    or ``reject``, or an ``overrun`` of Hypothesis's own budget of choices.
    """
    if warmup:
        sample(strategy, 3, seed, warmup=False)
    diagrams, observations = [], []

    @settings(
        max_examples=budget, database=None, deadline=None,
        phases=[Phase.generate], suppress_health_check=list(HealthCheck))
    @given(strategy)
    def run(diagram):
        diagrams.append(diagram)

    if seed is not None:
        run = hypothesis_seed(seed)(run)
    start = time.perf_counter()
    with with_observability_callback(observations.append):
        try:
            run()
        except Unsatisfiable:
            pass
    seconds = time.perf_counter() - start
    cases = [o for o in observations if o.type == "test_case"]
    gave_up = {}
    for case in cases:
        if case.status == "gave_up":
            reason = "overrun" if case.metadata.data_status.name == "OVERRUN"\
                else "rejected"
            gave_up[reason] = gave_up.get(reason, 0) + 1
    return diagrams, len(cases), gave_up, seconds


BOUNDARIES = {
    "free": lambda Ty: {},
    "fixed": lambda Ty: {"dom": Ty("a", "b"), "cod": Ty("b", "a")}
    if issubclass(Ty, monoidal.Ty) else {"dom": Ty("a"), "cod": Ty("b")},
}
""" The boundaries a sampler is asked for: none, or a fixed pair. """


def describe(diagrams, cases, gave_up, seconds):
    """ What every sampling experiment reports about a sample. """
    return {
        "cases": cases, "valid": len(diagrams), "gave_up": gave_up,
        "seconds": seconds,
        "distinct": len(set(map(shape, diagrams))),
        "coherent": len(set(map(coherent_shape, diagrams))),
        "sizes": [asdict(Size.of(d)) for d in diagrams]}


def log(*args):
    """ Print the progress of an experiment. """
    *names, row = args
    print(*names, f"{row['valid']}/{row['cases']}",
          f"{row['seconds']:.1f}s", file=sys.stderr)


def bracket(values, mean, target):
    """
    The value whose ``mean`` is the nearest to ``target``, trying ``values``
    coarse to fine: every other one from the smallest up, until the mean
    reaches the target, then those between the last two tried.
    """
    coarse = list(values[::2]) + list(values[-1:]) * (len(values) % 2 == 0)
    tried, above = [], None
    for value in coarse:
        tried.append(value)
        if mean(value) >= target:
            above = value
            break
    if above is not None and len(tried) > 1:
        low, high = values.index(tried[-2]), values.index(above)
        tried += values[low + 1:high]
    return min(tried, key=lambda v: abs(mean(v) - target))


def calibrate(task):
    """
    One cell of :func:`calibration`: for a doctrine and a sampler, the
    value of its knob nearest each target of :data:`MATCHED`.
    """
    doctrine, name, budget = task
    diagram, (key, values), means = diagram_class(doctrine), knob(name), {}

    def mean(value):
        if value not in means:
            diagrams, *_ = sample(
                getattr(diagram, f"strategy_{name}")(**{key: value}),
                budget, seed=0)
            means[value] = statistics.mean(
                Size.of(d).boxes for d in diagrams) if diagrams else 0.
        return means[value]

    rows = []
    with alphabet():
        for target in MATCHED:
            value = bracket(values, mean, target)
            rows.append({"doctrine": doctrine, "sampler": name,
                         "target": target, "params": {key: value},
                         "mean": means[value], "means": dict(means)})
    print(doctrine, name, means, file=sys.stderr)
    return rows


REUSE = None
"""
The calibration to reuse rather than compute, ``results/calibration.json``
with ``--reuse-calibration``.
"""


def calibration(mode):
    """
    For each doctrine, sampler and target of :data:`MATCHED`, the value of
    the parameter that sets its size, see :func:`knob`, whose mean number
    of boxes with free boundaries is the nearest to the target, from a
    sample of the calibration budget for each value tried, see
    :func:`bracket`, in parallel; or those of :data:`REUSE` if set.
    """
    if REUSE is not None:
        return [r for r in json.loads(REUSE.read_text())["rows"]
                if r["doctrine"] in doctrines()]
    return parallel(calibrate, [
        (doctrine, name, BUDGETS["calibration"][mode])
        for doctrine in doctrines() for name in implemented(doctrine)])


def regimes(doctrine, name):
    """
    The parameters a sampler is run with: its own defaults, then those
    calibrated to each target of :data:`MATCHED`, if calibrated, read from
    the output of this run or else from ``results/calibration.json``.
    """
    rows = load("calibration")
    if not rows and (RESULTS / "calibration.json").exists():
        rows = json.loads((RESULTS / "calibration.json").read_text())["rows"]
    found = {r["target"]: r["params"] for r in rows
             if r["doctrine"] == doctrine and r["sampler"] == name}
    return [("natural", {})] + [
        (f"matched {target:g}", found[target])
        for target in MATCHED if target in found]


def load(name):
    """ The rows of an experiment already run in this output, or none. """
    path = OUT / f"{name}.json"
    return json.loads(path.read_text())["rows"] if path.exists() else []


def measure(task):
    """
    One cell of :func:`throughput`: a doctrine and a sampler, under each
    of its regimes and boundaries.
    """
    doctrine, name, runs, budget = task
    diagram, rows = diagram_class(doctrine), []
    method = getattr(diagram, f"strategy_{name}")
    with alphabet():
        for regime, params in runs:
            for boundary, bounds in BOUNDARIES.items():
                if regime != "natural" and boundary != "free":
                    continue
                result = sample(method(**params, **bounds(diagram.ob)),
                                budget, seed=0)
                rows.append({"doctrine": doctrine, "sampler": name,
                             "regime": regime, "params": params,
                             "boundary": boundary, **describe(*result)})
                log(doctrine, name, regime, boundary, rows[-1])
    return rows


def throughput(mode):
    """
    For each doctrine, sampler and boundary, the valid diagrams and why the
    others were rejected, the valid diagrams per second, their sizes and
    how many are distinct, syntactically and up to coherence: with its own
    parameters, and with those calibrated to each mean size, free boundaries
    only, since that is what the calibration matches; one process for each
    doctrine and sampler, so that speeds are those of one core each.
    """
    return parallel(measure, [
        (doctrine, name, regimes(doctrine, name),
         BUDGETS["throughput"][mode])
        for doctrine in doctrines() for name in implemented(doctrine)])


def matrix(mode):
    """
    Run the cells of the property matrix of each doctrine under each of
    its samplers, with a fixed seed, and collect the outcome of each cell,
    its distinct draws and, for a failure, the first line of its message;
    on the first two doctrines only for a smoke run.
    """
    rows = []
    for doctrine in doctrines()[:2] if mode == "smoke" else doctrines():
        prefix = factory_name(diagram_class(doctrine)) + "."
        for name in implemented(doctrine):
            report = OUT / "raw" / f"matrix-{doctrine}-{name}.json"
            junit = report.with_suffix(".xml")
            start = time.perf_counter()
            subprocess.run([
                sys.executable, "-m", "pytest", "proptest/test_axioms.py",
                "-q", "-p", "no:benchmark", "-p", "no:cacheprovider",
                "-n", "auto", "--hypothesis-seed=0", "-k", prefix,
                f"--proptest-report={report}", f"--junitxml={junit}"],
                env=os.environ | {"HYPOTHESIS_PROFILE": PROFILES[mode],
                                  "PROPTEST_SAMPLER": name},
                cwd=HERE.parent, capture_output=True, check=False)
            seconds = time.perf_counter() - start
            failures = {
                case.get("name").split("[", 1)[1][:-1]:
                (case.find("failure").get("message") or "").split("\n")[0]
                for case in ET.parse(junit).iter("testcase")
                if case.find("failure") is not None}
            cells = {key: cell for key, cell
                     in json.loads(report.read_text()).items()
                     if key.startswith(prefix)}
            rows.append({
                "doctrine": doctrine, "sampler": name,
                "seconds": seconds, "cells": {
                    key: dict(cell, message=failures.get(key))
                    for key, cell in cells.items()}})
            print(doctrine, name, f"{seconds:.0f}s", file=sys.stderr)
    return rows


SIZES = (2., 4., 8., 16., 32., float("inf"))
""" The expected numbers of nodes the Boltzmann sampler is tuned to. """


def boltzmann(mode):
    """
    For each doctrine, the grammar of the Boltzmann sampler: its size and
    singularity, then for each expected size, the parameter it is tuned to,
    the expected number of generators and what it draws, at the critical
    parameter included, by choices Hypothesis shrinks or exactly.
    """
    rows = []
    for doctrine in doctrines():
        diagram = diagram_class(doctrine)
        if not hasattr(diagram, "grammar_atoms"):
            continue
        start = time.perf_counter()
        grammar = Grammar.compile(
            diagram, diagram.grammar_atoms, diagram.grammar_width)
        compiled = time.perf_counter() - start
        rho, root = grammar.singularity(), grammar.root()
        kinds = {}
        for production in grammar.productions:
            kinds[production.kind] = kinds.get(production.kind, 0) + 1
        for exact in (False, True):
            for size in SIZES:
                z = grammar.tune(size, root)
                result = sample(
                    grammar.strategy(size=size, exact=exact),
                    BUDGETS["boltzmann"][
                        mode if doctrine in ORIGINAL or mode != "full"
                        else "quick"])
                rows.append({
                    "doctrine": doctrine, "size": size, "exact": exact,
                    "z": z, "rho": rho,
                    "expected": grammar.expected_size(z, root),
                    "generators": expected_generators(grammar, z, root),
                    "nonterminals": len(grammar.nonterminals),
                    "productions": kinds, "compile_seconds": compiled,
                    **describe(*result)})
                log(doctrine, size, exact, rows[-1])
    return rows


def expected_generators(grammar, z, root):
    """
    The expected number of generators of a derivation, the logarithmic
    derivative of the generating function in the bias of generators.
    """
    step = 1e-5
    low, high = (math.log(root @ grammar.values(z, {"generator": u}))
                 for u in (1 - step, 1 + step))
    return (high - low) / (2 * step)


TARGETS = {"node": 12., "generator": 4., "braiding": 1., "trace_right": .5}
"""
The expected counts the convex tuning aims at: nodes, generators, swaps and
traces of a symmetric derivation.
"""


def convex(mode):
    """
    Tune the Boltzmann sampler of symmetric diagrams to the expected count
    of each kind in :data:`TARGETS` at once, as a convex problem (Bendkowski,
    Bodini, Dovgal 2018), then count what it derives, outside Hypothesis,
    against the sampler tuned to the expected number of nodes alone.
    """
    import cvxpy as cp  # pylint: disable=import-outside-toplevel
    from scipy import sparse  # pylint: disable=import-outside-toplevel

    diagram = symmetric.Diagram
    grammar = Grammar.compile(
        diagram, diagram.grammar_atoms, diagram.grammar_width)
    kinds = [kind for kind in TARGETS if kind != "node"]
    n, k = len(grammar.nonterminals), len(kinds)
    entries = [
        (i, j) for i, p in enumerate(grammar.productions)
        for j in [0] + [1 + kinds.index(p.kind) for _ in [p] if p.kind in kinds]
        + [1 + k + c for c in p.children]]
    rows, cols = zip(*entries)
    exponents = sparse.csr_matrix(
        (np.ones(len(entries)), (rows, cols)),
        shape=(len(grammar.productions), 1 + k + n))
    x, top = cp.Variable(1 + k + n), cp.Variable()
    terms = exponents @ x
    by_lhs = [[] for _ in range(n)]
    for i, production in enumerate(grammar.productions):
        by_lhs[production.lhs].append(i)
    constraints = [
        cp.log_sum_exp(cp.hstack([terms[i] for i in indices])) <= x[1 + k + j]
        for j, indices in enumerate(by_lhs) if indices]
    constraints.append(cp.log_sum_exp(x[1 + k:]) <= top)
    targets = np.array([TARGETS["node"]] + [TARGETS[kind] for kind in kinds])
    problem = cp.Problem(cp.Minimize(top - targets @ x[:1 + k]), constraints)
    start = time.perf_counter()
    problem.solve(solver="CLARABEL")
    seconds = time.perf_counter() - start
    z = float(np.exp(x.value[0]))
    bias = {kind: float(np.exp(x.value[1 + i])) for i, kind in enumerate(kinds)}

    budget = 10 * BUDGETS["boltzmann"][mode]
    plain = grammar.tune(TARGETS["node"], grammar.root())
    return [{"status": problem.status, "seconds": seconds, "z": z,
             "rho": grammar.singularity(), "bias": bias, "targets": TARGETS,
             "tuned": simulate(grammar, z, bias, budget),
             "plain": simulate(grammar, plain, None, budget)}]


def simulate(grammar, z, bias, budget, max_nodes=10_000):
    """
    The mean count of each kind of production in ``budget`` derivations
    drawn by the Boltzmann sampler of the grammar with true randomness,
    outside Hypothesis, those larger than ``max_nodes`` left out.
    """
    rng = np.random.default_rng(0)
    values = grammar.values(z, bias)
    n = len(values)
    extended = np.append(values, 1.)
    terms = grammar.weights(z, bias) * extended[np.array([
        p.children + (n, ) * (2 - len(p.children))
        for p in grammar.productions])].prod(axis=1)
    by_lhs = [[] for _ in range(n)]
    for i, production in enumerate(grammar.productions):
        by_lhs[production.lhs].append(i)
    totals, kept = {}, 0
    for _ in range(budget):
        counts, stack = {"node": 0}, [rng.choice(
            n, p=grammar.root() * values / (grammar.root() @ values))]
        while stack and counts["node"] <= max_nodes:
            candidates = by_lhs[stack.pop()]
            weights = terms[candidates]
            production = grammar.productions[candidates[rng.choice(
                len(candidates), p=weights / weights.sum())]]
            counts["node"] += 1
            counts[production.kind] = counts.get(production.kind, 0) + 1
            stack.extend(production.children)
        if counts["node"] <= max_nodes:
            kept += 1
            for kind, count in counts.items():
                totals[kind] = totals.get(kind, 0) + count
    return {kind: count / kept for kind, count in totals.items()}


LAWS = "symmetric"
""" The doctrine whose laws the mutants are checked against. """


def falsify(law, budget, seed=0, mutant=None):
    """
    Search for a counterexample to a law, as ``Axiom.falsify`` does, within
    ``budget`` examples from a ``seed``: arguments on which the law fails,
    with the code of a ``mutant`` if given, and holds without it, so that
    only a failure the mutant causes counts. Return the shrunk arguments,
    the examples drawn before the first one, and the calls and seconds
    spent shrinking it; or the exception that stopped the search, which is
    the sampler crashing on the mutated code; or :obj:`None` if none.
    """
    calls, first, start = [0], [None], [None]

    def holds(arguments):
        try:
            return bool(law(**arguments))
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def fails(sequent):
        calls[0] += 1
        if holds(sequent[1]):
            return False
        if mutant is not None:
            with mutant.reverted():
                if not holds(sequent[1]):
                    return False
        if first[0] is None:
            first[0], start[0] = calls[0], time.perf_counter()
        return True

    try:
        _, arguments = find(
            law.sequents(**law.params), fails, random=random.Random(seed),
            settings=settings(
                max_examples=budget, database=None, deadline=None,
                suppress_health_check=list(HealthCheck)))
    except (NoSuchExample, Unsatisfiable):
        return None
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {"crash": type(error).__name__, "examples": calls[0]}
    terms = [v for v in arguments.values() if isinstance(v, cat.Arrow)]
    return {"crash": None, "examples": first[0],
            "shrink_calls": calls[0] - first[0],
            "shrink_seconds": time.perf_counter() - start[0],
            "shrunk": [asdict(Size.of(t)) for t in terms],
            "arguments": {key: FRESH.sub("f", str(value))
                          for key, value in arguments.items()}}


def checked_laws(diagram):
    """ The laws of a class that apply and are not declared broken. """
    return [law for law in Testable.matrix() if law.category is diagram
            and law.applicable and not law.broken]


@contextmanager
def glue_counter(counts):
    """
    Count the boundaries the grammar is asked for, and those it does not
    derive, which a generator glues, in a block.
    """
    old = Grammar.strategy

    def strategy(self, dom=None, cod=None, **params):
        counts["asked"] += 1
        counts["glued"] += any(
            x is not None and x not in self.types for x in (dom, cod))
        return old(self, dom=dom, cod=cod, **params)

    Grammar.strategy = strategy
    try:
        yield
    finally:
        Grammar.strategy = old


def hunt(task):
    """
    One run of the mutants experiment: under a sampler, with the given
    parameters and seed, for each mutant, the first law of :data:`LAWS`
    that it makes fail, the examples drawn until then, and the shrinking.
    """
    name, regime, params, seed, budget = task
    diagram, rows = diagram_class(LAWS), []
    laws = checked_laws(diagram)
    with alphabet(), calibrated(diagram, name, params):
        for mutant in MUTANTS:
            counts = {"asked": 0, "glued": 0}
            start, drawn, kill, crash = time.perf_counter(), 0, None, None
            with mutant.applied(), glue_counter(counts):
                for law in laws:
                    found = falsify(law, budget, seed, mutant)
                    if found is not None and found["crash"]:
                        crash, drawn = dict(found, law=law.name),\
                            drawn + found["examples"]
                        break
                    if found is not None:
                        kill, drawn = dict(found, law=law.name),\
                            drawn + found["examples"]
                        break
                    drawn += budget
            rows.append({
                "mutant": mutant.name, "sampler": name, "regime": regime,
                "params": params, "seed": seed, "kill": kill, "crash": crash,
                "examples": drawn, "glue": counts,
                "seconds": time.perf_counter() - start})
    return rows


def mutants(mode):
    """
    For each sampler of :data:`LAWS` but the rejecting baseline, with its
    own parameters and calibrated to the first of :data:`MATCHED`, and for
    each of :data:`SEEDS` seeds: the first law each mutant makes fail, see
    :func:`hunt`, in parallel, one process for each run.
    """
    budget, tasks = BUDGETS["mutants"][mode], []
    for name in implemented(LAWS):
        if name == "representational_baseline":
            continue
        for regime, params in regimes(LAWS, name)[:2]:
            tasks += [(name, regime, params, seed, budget)
                      for seed in range(SEEDS[mode])]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(WORKERS) as pool:
        for found in pool.map(hunt, tasks):
            rows += found
            print(found[0]["sampler"], found[0]["regime"], found[0]["seed"],
                  [r["kill"] and r["kill"]["law"] for r in found],
                  file=sys.stderr)
    return rows


DIMS = {"a": 2, "b": 3}
""" The dimension of each atom in the semantic experiment. """


def signature():
    """
    The fixed signature of the semantic experiment, symmetric boxes with a
    random integer tensor for each, and the functor that evaluates them.
    """
    a, b = symmetric.Ty("a"), symmetric.Ty("b")
    boxes = [symmetric.Box(name, dom, cod) for name, dom, cod in (
        ("f", a, b), ("g", b, a @ a), ("h", a @ b, symmetric.Ty()),
        ("k", symmetric.Ty(), a), ("m", a @ a, a))]
    rng = np.random.default_rng(0)
    functor = tensor.Functor(
        {a: DIMS["a"], b: DIMS["b"]},
        {box: rng.integers(-2, 3, size=int(np.prod(
            [DIMS[x.name] for x in box.dom.inside + box.cod.inside])))
         for box in boxes}, dom=symmetric.Diagram, dtype=int)
    return boxes, functor


@contextmanager
def fixed_signature(boxes):
    """
    Restrict the free symmetric category to the boxes of a signature and its
    types to their atoms, in a block: a sampler asking for a box of a type
    no generator has is rejected, since a semantic category cannot invent
    it, and the grammar only has the generators of the signature.
    """
    by_type = {}
    for box in boxes:
        by_type.setdefault((box.dom, box.cod), []).append(box)
    old_box = symmetric.Box.__dict__.get("strategy")
    old_generators = cat.GENERATORS
    old_signature = symmetric.Diagram.grammar_signature

    def strategy(cls, *, types=None, dom=None, cod=None):
        # pylint: disable=unused-argument  # the types are the signature's
        found = [box for (x, y), group in by_type.items()
                 for box in group if dom in (None, x) and cod in (None, y)]
        return st.sampled_from(found) if found else st.nothing()

    symmetric.Box.strategy = classmethod(strategy)
    cat.GENERATORS = tuple(DIMS)
    symmetric.Diagram.grammar_signature = tuple(by_type)
    try:
        yield
    finally:
        if old_box is None:
            del symmetric.Box.strategy
        else:
            symmetric.Box.strategy = old_box
        cat.GENERATORS = old_generators
        symmetric.Diagram.grammar_signature = old_signature


def evaluate(functor, diagram):
    """
    The tensor of a diagram, or :obj:`None` if it has a box the functor does
    not map, e.g. a delayed box.
    """
    try:
        return functor(diagram).array
    except KeyError:
        return None


def semantic(mode):
    """
    For each sampler of symmetric diagrams over a fixed signature, the valid
    diagrams, the time to sample and evaluate them as tensors, how many the
    functor cannot evaluate and how many distinct tensors they denote.
    """
    boxes, functor = signature()
    a = symmetric.Ty("a")
    rows = []
    with fixed_signature(boxes):
        for name in implemented("symmetric"):
            for boundary, bounds in (("free", {}),
                                     ("fixed", {"dom": a, "cod": a @ a})):
                method = getattr(symmetric.Diagram, f"strategy_{name}")
                diagrams, cases, gave_up, seconds = sample(
                    method(**bounds), BUDGETS["semantic"][mode])
                start = time.perf_counter()
                arrays = [evaluate(functor, d) for d in diagrams]
                evaluated = time.perf_counter() - start
                unevaluable = sum(x is None for x in arrays)
                arrays = [x for x in arrays if x is not None]
                rows.append({
                    "sampler": name, "boundary": boundary, "cases": cases,
                    "valid": len(diagrams), "gave_up": gave_up,
                    "seconds": seconds, "evaluation_seconds": evaluated,
                    "unevaluable": unevaluable,
                    "tensors": len({(x.shape, x.tobytes()) for x in arrays}),
                    "zero": sum(not x.any() for x in arrays),
                    "sizes": [asdict(Size.of(d)) for d in diagrams]})
                log(name, boundary, rows[-1])
    return rows


UNIFORMS = {
    "integers(0, 2**20)": st.integers(0, 2 ** 20 - 1).map(lambda i: i / 2 ** 20),
    "a byte among 20": st.lists(st.integers(0, 255), min_size=20,
                                max_size=20).map(lambda xs: xs[10] / 256),
    "floats(0, 1)": st.floats(0, 1, exclude_max=True),
    "randoms()": st.randoms().map(lambda r: r.random()),
    "randoms(true)": st.randoms(use_true_random=True).map(
        lambda r: r.random()),
}
""" Ways of drawing a number in ``[0, 1)`` with Hypothesis. """


def uniforms(mode):
    """
    How far each way of drawing a number in ``[0, 1)`` is from uniform:
    the share of draws below 0.01, 0.1 and 0.5, against 1%, 10% and 50%.
    """
    rows = []
    for name, strategy in UNIFORMS.items():
        draws = []

        @settings(max_examples=BUDGETS["uniforms"][mode], database=None,
                  phases=[Phase.generate],
                  suppress_health_check=list(HealthCheck))
        @given(strategy)
        def run(x):
            draws.append(x)  # pylint: disable=cell-var-from-loop

        run()
        rows.append({"strategy": name, "draws": len(draws), **{
            f"below {q}": float(np.mean(np.array(draws) < q))
            for q in (.01, .1, .5)}})
    return rows


EXPERIMENTS = {
    "calibration": calibration,
    "uniforms": uniforms,
    "throughput": throughput, "boltzmann": boltzmann, "convex": convex,
    "semantic": semantic, "mutants": mutants, "matrix": matrix}


def merge(shards):
    """
    Concatenate the rows of each experiment over the given shards, i.e.
    ``results/<shard>/<experiment>.json``, into ``results/<experiment>.json``,
    and copy their raw reports into ``results/raw``.
    """
    names = sorted({path.stem for shard in shards
                    for path in (RESULTS / shard).glob("*.json")})
    for name in names:
        found = [json.loads(path.read_text()) for shard in shards
                 for path in [RESULTS / shard / f"{name}.json"]
                 if path.exists()]
        path = RESULTS / f"{name}.json"
        path.write_text(json.dumps({
            "mode": found[0]["mode"],
            "seconds": sum(f["seconds"] for f in found),
            "rows": [row for f in found for row in f["rows"]]},
            indent=1, default=float))
        print(f"wrote {path} from {len(found)} shard(s)", file=sys.stderr)
    (RESULTS / "raw").mkdir(parents=True, exist_ok=True)
    for shard in shards:
        for raw in (RESULTS / shard / "raw").glob("*"):
            (RESULTS / "raw" / raw.name).write_bytes(raw.read_bytes())


def main():
    """ Run the experiments asked for and write their results. """
    global OUT, SELECTED, REUSE  # pylint: disable=global-statement
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_const", const="quick",
                      dest="mode", default="quick")
    mode.add_argument("--full", action="store_const", const="full",
                      dest="mode")
    mode.add_argument("--smoke", action="store_const", const="smoke",
                      dest="mode")
    parser.add_argument(
        "experiments", nargs="*",
        help="the experiments to run, by default all of them, but those of "
             "QUICK_ONLY for a full run")
    parser.add_argument(
        "--doctrines", type=lambda text: text.split(","),
        help="the doctrines to run on, separated by commas, e.g. "
             "monoidal,symmetric")
    parser.add_argument(
        "--out", metavar="NAME",
        help="write to results/NAME/<experiment>.json, a shard")
    parser.add_argument(
        "--reuse-calibration", action="store_true",
        help="copy results/calibration.json rather than calibrate again")
    parser.add_argument(
        "--merge", nargs="+", metavar="NAME",
        help="concatenate the shards NAME into results/<experiment>.json")
    args = parser.parse_args()
    if args.merge:
        merge(args.merge)
        return
    SELECTED = args.doctrines
    REUSE = RESULTS / "calibration.json" if args.reuse_calibration else None
    OUT = RESULTS / "smoke" if args.mode == "smoke" else RESULTS
    OUT = OUT / args.out if args.out else OUT
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    names = args.experiments or [
        name for name in EXPERIMENTS
        if args.mode != "full" or name not in QUICK_ONLY]
    for name in names:
        start = time.perf_counter()
        with alphabet():
            rows = EXPERIMENTS[name](args.mode)
        path = OUT / f"{name}.json"
        path.write_text(json.dumps({
            "mode": args.mode, "seconds": time.perf_counter() - start,
            "rows": rows}, indent=1, default=float))
        print(f"wrote {path} in {time.perf_counter() - start:.0f}s",
              file=sys.stderr)


if __name__ == "__main__":
    main()
