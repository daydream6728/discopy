"""
Experiments comparing the samplers of string diagrams, see ``analysis.md``.

Each experiment writes its raw results to ``sampling/results/<name>.json``,
which ``analysis.md`` and ``presentation.md`` read: neither runs an
experiment.

    uv run --with cvxpy python sampling/experiments.py --quick
    uv run --with cvxpy python sampling/experiments.py --quick boltzmann

``--quick`` is the budget the notebooks are regenerated with, ``--full`` the
one a long background run uses.
"""

import argparse
import json
import math
import os
import pathlib
import re
import subprocess
import sys
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

from discopy import cat, compact, markov, monoidal, symmetric, tensor
from discopy.abc import SymmetricCategory
from discopy.boltzmann import Grammar
from discopy.testable import Testable

HERE = pathlib.Path(__file__).parent
RESULTS = HERE / "results"
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
)
""" The samplers, by the name of their method ``strategy_<sampler>``. """

DOCTRINES = {
    "monoidal": (monoidal, 1),
    "symmetric": (symmetric, 1),
    "markov": (markov, 1),
    "compact": (compact, 1),
    "braided": ("braided", 2),
    "balanced": ("balanced", 2),
    "traced": ("traced", 2),
    "rigid": ("rigid", 2),
    "pivotal": ("pivotal", 2),
    "frobenius": ("frobenius", 2),
    "feedback": ("feedback", 2),
    "closed": ("closed", 2),
}
"""
Every doctrine, with the round it is studied in: a round-two doctrine is
named, not imported, so that it reads as a stub until its turn.
"""

BUDGETS = {
    "throughput": {"quick": 200, "full": 2000},
    "boltzmann": {"quick": 300, "full": 3000},
    "mutants": {"quick": 30, "full": 300},
    "semantic": {"quick": 200, "full": 2000},
    "uniforms": {"quick": 2000, "full": 20000},
}
""" Examples per cell of each experiment. """

PROFILES = {"quick": "pr", "full": "explore"}
""" The Hypothesis profile the property matrix is run under. """

FRESH = re.compile(r"f_[0-9a-f]{32}")
""" The name of a fresh box, see :meth:`discopy.cat.Box.strategy`. """


def diagram_class(doctrine):
    """ The diagrams of a doctrine studied in this round, else ``None``. """
    module, _ = DOCTRINES[doctrine]
    return None if isinstance(module, str) else module.Diagram


def implemented(doctrine):
    """ The samplers a doctrine of this round implements. """
    diagram = diagram_class(doctrine)
    return [s for s in SAMPLERS if hasattr(diagram, f"strategy_{s}")]


def round_one():
    """ The doctrines of this round. """
    return [d for d, (_, round_) in DOCTRINES.items() if round_ == 1]


@contextmanager
def sampler(diagram, name):
    """ Sample the diagrams of a class by the given sampler, in a block. """
    old = diagram.__dict__.get("sampler")
    diagram.sampler = name
    try:
        yield
    finally:
        if old is None:
            del diagram.sampler
        else:
            diagram.sampler = old


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
            width=max([len(diagram.dom), len(diagram.cod)] + [
                len(layer.dom) for layer in diagram.inside]),
            crossings=sum(inversions(list(box.perm)) for box in perms),
            structural=len(boxes) - len(generators) - len(perms))


def flatten(diagram):
    """ The boxes of a diagram, those inside a trace or a bubble included. """
    for box in diagram.boxes:
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


def coherent_shape(diagram):
    """
    A diagram up to the names of its fresh boxes and up to coherence: the
    Weisfeiler-Lehman hash of its hypergraph for a symmetric category,
    which isomorphic hypergraphs share, else its planar normal form, when
    it is boundary-connected and has one.
    """
    if not isinstance(diagram, SymmetricCategory):
        try:
            return shape(diagram.normal_form())
        except NotImplementedError:
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


def sample(strategy, budget, seed=None):
    """
    Run ``strategy`` for ``budget`` examples in the generate phase only,
    from a ``seed`` if given so that the draws are reproducible, and
    return each valid diagram with the time it took and the count of test
    cases Hypothesis gave up on, by reason: ``rejected`` by the sampler, a
    failed ``assume`` or ``reject``, or an ``overrun`` of Hypothesis's own
    budget of choices.
    """
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
    "fixed": lambda Ty: {"dom": Ty("a", "b"), "cod": Ty("b", "c")},
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


def throughput(mode):
    """
    For each doctrine, sampler and boundary, the valid diagrams and why the
    others were rejected, the valid diagrams per second, their sizes and
    how many are distinct, syntactically and up to coherence.
    """
    rows = []
    for doctrine in round_one():
        diagram = diagram_class(doctrine)
        for name in implemented(doctrine):
            for boundary, bounds in BOUNDARIES.items():
                method = getattr(diagram, f"strategy_{name}")
                result = sample(method(**bounds(diagram.ob)),
                                BUDGETS["throughput"][mode])
                rows.append({"doctrine": doctrine, "sampler": name,
                             "boundary": boundary, **describe(*result)})
                log(doctrine, name, boundary, rows[-1])
    return rows


def matrix(mode):
    """
    Run the cells of the property matrix of each doctrine under each of
    its samplers, with a fixed seed, and collect the outcome of each cell,
    its distinct draws and, for a failure, the first line of its message.
    """
    rows = []
    for doctrine in round_one():
        prefix = f"{doctrine}.Diagram."
        for name in implemented(doctrine):
            report = RESULTS / "raw" / f"matrix-{doctrine}-{name}.json"
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
    for doctrine in round_one():
        diagram = diagram_class(doctrine)
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
                result = sample(grammar.strategy(size=size, exact=exact),
                                BUDGETS["boltzmann"][mode])
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


def falsify(law, budget):
    """
    Search for a counterexample to a law, as ``Axiom.falsify`` does, within
    ``budget`` examples, counting those drawn before the first one: its
    shrunk arguments, the count and whether it was a crash in the sampler,
    or :obj:`None` if none was found.
    """
    calls, first = [0], [None]

    def fails(sequent):
        calls[0] += 1
        try:
            holds = bool(law(**sequent[1]))
        except Exception:  # pylint: disable=broad-exception-caught
            holds = False
        if not holds and first[0] is None:
            first[0] = calls[0]
        return not holds

    try:
        _, arguments = find(law.sequents(**law.params), fails, settings=(
            settings(max_examples=budget, database=None, deadline=None,
                     suppress_health_check=list(HealthCheck))))
    except (NoSuchExample, Unsatisfiable):
        return None
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {"crash": type(error).__name__, "examples": calls[0]}
    terms = [v for v in arguments.values() if isinstance(v, cat.Arrow)]
    return {"crash": None, "examples": first[0], "shrunk": [
        asdict(Size.of(t)) for t in terms], "arguments": {
            key: FRESH.sub("f", str(value))
            for key, value in arguments.items()}}


def checked_laws(diagram):
    """ The laws of a class that apply and are not declared broken. """
    return [law for law in Testable.matrix() if law.category is diagram
            and law.applicable and not law.broken]


def mutants(mode):
    """
    For each sampler of :data:`LAWS` but the rejecting baseline, the laws
    that fail with no mutant, then for each mutant the first law that fails
    besides those, the examples drawn until then and the shrunk
    counterexample.
    """
    diagram, budget = diagram_class(LAWS), BUDGETS["mutants"][mode]
    laws, rows = checked_laws(diagram), []
    names = [s for s in implemented(LAWS) if s != "representational_baseline"]
    for name in names:
        with sampler(diagram, name):
            natural = [law.name for law in laws if falsify(law, budget)]
            rows.append({"mutant": None, "sampler": name, "fails": natural})
            print("baseline", name, natural, file=sys.stderr)
            for mutant in MUTANTS:
                start, drawn, kill = time.perf_counter(), 0, None
                with mutant.applied():
                    for law in laws:
                        if law.name in natural:
                            continue
                        found = falsify(law, budget)
                        if found is not None:
                            kill = dict(found, law=law.name)
                            drawn += found["examples"]
                            break
                        drawn += budget
                rows.append({
                    "mutant": mutant.name, "sampler": name, "kill": kill,
                    "examples": drawn,
                    "seconds": time.perf_counter() - start})
                print(mutant.name, name, kill and kill["law"],
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
    "uniforms": uniforms,
    "throughput": throughput, "boltzmann": boltzmann, "convex": convex,
    "semantic": semantic, "mutants": mutants, "matrix": matrix}


def main():
    """ Run the experiments asked for and write their results. """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_const", const="quick",
                      dest="mode", default="quick")
    mode.add_argument("--full", action="store_const", const="full",
                      dest="mode")
    parser.add_argument("experiments", nargs="*", default=list(EXPERIMENTS))
    args = parser.parse_args()
    (RESULTS / "raw").mkdir(parents=True, exist_ok=True)
    for name in args.experiments:
        start = time.perf_counter()
        rows = EXPERIMENTS[name](args.mode)
        path = RESULTS / f"{name}.json"
        path.write_text(json.dumps({
            "mode": args.mode, "seconds": time.perf_counter() - start,
            "rows": rows}, indent=1, default=float))
        print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
