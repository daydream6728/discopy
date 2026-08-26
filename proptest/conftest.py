"""
Adaptive example budgets for the property suite, see PROPTEST.md.

Before a Hypothesis cell runs, its budget is looked up in the
:class:`discopy.testing.Ledger` of the cell's own pass/fail history:
flaky cells search harder, long-stable ones wind down, the rest keep the
budget written in their decorator. After it runs, its outcome is recorded
and the ledger saved, locally in ``.hypothesis`` and across CI jobs as
the ``proptest-ledger`` artifact.

The budget is swapped into the slot where ``@settings`` stores its
decoration and Hypothesis reads the settings of each run — its only
per-cell seam, the profile machinery being global and bound at import.
"""

from hypothesis import settings

from discopy.testing import Ledger

LEDGER = Ledger.load()
WRITTEN = {}
TRACKED = set()


def pytest_runtest_setup(item):
    function = getattr(item, "function", None)
    if not hasattr(function, "hypothesis"):
        return
    written = WRITTEN.setdefault(
        function, function._hypothesis_internal_use_settings or settings())
    function._hypothesis_internal_use_settings = settings(
        written,
        max_examples=LEDGER.budget(item.nodeid, written.max_examples))
    TRACKED.add(item.nodeid)


def pytest_runtest_logreport(report):
    if report.when == "call" and report.nodeid in TRACKED:
        LEDGER.record(report.nodeid, report.passed)


def pytest_sessionfinish(session):
    if TRACKED:
        LEDGER.save()
