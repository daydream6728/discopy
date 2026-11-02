"""
Experiments comparing the samplers of string diagrams, see ``presentation.md``.

Each experiment writes its raw results to ``sampling/results/<name>.json``,
which ``presentation.md`` reads: the slides never run an experiment.

    uv run python sampling/experiments.py --quick            # every experiment
    uv run python sampling/experiments.py --quick throughput # just one

``--quick`` is the budget the slides are regenerated with, minutes in all,
``--full`` the one a long background run uses.
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass

from hypothesis import HealthCheck, Phase, given, settings
from hypothesis.errors import Unsatisfiable
from hypothesis.internal.observability import with_observability_callback

from discopy import compact, markov, monoidal, symmetric

HERE = pathlib.Path(__file__).parent
RESULTS = HERE / "results"

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

BUDGETS = {"quick": 200, "full": 2000}
""" Examples per cell of the throughput experiment. """

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


@dataclass
class Size:
    """ The sizes of a diagram, see the slide on metrics. """
    boxes: int
    layers: int
    width: int
    crossings: int
    structural: int

    @staticmethod
    def of(diagram):
        """
        Count the generators, i.e. the fresh boxes, the layers, the widest
        boundary, the crossings, i.e. the inversions of each permutation,
        and the other structural boxes, e.g. copies or cups.
        """
        boxes = diagram.boxes
        perms = [box for box in boxes if hasattr(box, "perm")]
        generators = [box for box in boxes if FRESH.fullmatch(box.name)]
        return Size(
            boxes=len(generators),
            layers=len(diagram),
            width=max([len(diagram.dom), len(diagram.cod)] + [
                len(layer.dom) for layer in diagram.inside]),
            crossings=sum(inversions(list(box.perm)) for box in perms),
            structural=len(boxes) - len(generators) - len(perms))


def inversions(xs):
    """ The number of pairs out of order, i.e. of crossings. """
    return sum(x > y for i, x in enumerate(xs) for y in xs[i + 1:])


def shape(diagram):
    """ A diagram up to the names of its fresh boxes. """
    return FRESH.sub("f", repr(diagram))


def sample(strategy, budget):
    """
    Run ``strategy`` for ``budget`` examples in the generate phase only, and
    return each valid diagram with the time it took and the count of test
    cases Hypothesis gave up on, by reason, e.g. a failed ``assume``.
    """
    diagrams, observations = [], []

    @settings(
        max_examples=budget, database=None, deadline=None,
        phases=[Phase.generate], suppress_health_check=list(HealthCheck))
    @given(strategy)
    def run(diagram):
        diagrams.append(diagram)

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
            reason = case.status_reason or case.metadata.data_status.name
            gave_up[reason] = gave_up.get(reason, 0) + 1
    return diagrams, len(cases), gave_up, seconds


BOUNDARIES = {
    "free": lambda Ty: {},
    "fixed": lambda Ty: {"dom": Ty("a", "b"), "cod": Ty("b", "c")},
}
""" The boundaries a sampler is asked for: none, or a fixed pair. """


def throughput(budget):
    """
    For each doctrine, sampler and boundary, the rate of valid diagrams,
    why the others were rejected, the valid diagrams per second, their
    sizes and how many distinct shapes they have.
    """
    rows = []
    for doctrine, (_, round_) in DOCTRINES.items():
        if round_ > 1:
            continue
        diagram = diagram_class(doctrine)
        for sampler in implemented(doctrine):
            for boundary, bounds in BOUNDARIES.items():
                method = getattr(diagram, f"strategy_{sampler}")
                diagrams, cases, gave_up, seconds = sample(
                    method(**bounds(diagram.ob)), budget)
                rows.append({
                    "doctrine": doctrine, "sampler": sampler,
                    "boundary": boundary, "cases": cases,
                    "valid": len(diagrams), "gave_up": gave_up,
                    "seconds": seconds,
                    "distinct": len(set(map(shape, diagrams))),
                    "sizes": [asdict(Size.of(d)) for d in diagrams]})
                print(doctrine, sampler, boundary, f"{len(diagrams)}/{cases}",
                      f"{seconds:.1f}s", file=sys.stderr)
    return rows


def matrix(profile, doctrines=("symmetric", )):
    """
    Run the cells of the property matrix of each doctrine under each of
    its samplers, with a fixed seed, and collect the outcome of each cell,
    its distinct draws and, for a failure, the first line of its message.
    """
    rows = []
    for doctrine in doctrines:
        prefix = f"{doctrine}.Diagram."
        for sampler in implemented(doctrine):
            report = RESULTS / "raw" / f"matrix-{doctrine}-{sampler}.json"
            junit = report.with_suffix(".xml")
            start = time.perf_counter()
            subprocess.run([
                sys.executable, "-m", "pytest", "proptest/test_axioms.py",
                "-q", "-p", "no:benchmark", "-p", "no:cacheprovider",
                "--hypothesis-seed=0", "-k", prefix,
                f"--proptest-report={report}", f"--junitxml={junit}"],
                env=os.environ | {"HYPOTHESIS_PROFILE": profile,
                                  "PROPTEST_SAMPLER": sampler},
                cwd=HERE.parent, capture_output=True, check=False)
            seconds = time.perf_counter() - start
            failures = {
                case.get("name").split("[", 1)[1][:-1]:
                (case.find("failure").get("message") or "").split("\n")[0]
                for case in ET.parse(junit).iter("testcase")
                if case.find("failure") is not None}
            cells = {name: cell for name, cell
                     in json.loads(report.read_text()).items()
                     if name.startswith(prefix)}
            rows.append({
                "doctrine": doctrine, "sampler": sampler,
                "seconds": seconds, "cells": {
                    name: dict(cell, message=failures.get(name))
                    for name, cell in cells.items()}})
            print(doctrine, sampler, f"{seconds:.0f}s", file=sys.stderr)
    return rows


EXPERIMENTS = {
    "throughput": lambda mode: throughput(BUDGETS[mode]),
    "matrix": lambda mode: matrix(PROFILES[mode]),
}


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
        rows = EXPERIMENTS[name](args.mode)
        path = RESULTS / f"{name}.json"
        path.write_text(json.dumps(
            {"mode": args.mode, "rows": rows}, indent=1))
        print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
