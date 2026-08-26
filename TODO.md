# TODO

> in a new worktree, implement an adaptative property test allocation
> strategy based on a cross-run database that would live as a database
> locally and updated across CI jobs as artifacts. the goal is to reduce
> the running time of the property testing suite and put more effort into
> generating counter examples for tests that are known to be flaky. i'm
> not sure exactly whats the right way to do it. i want it to be fully
> automatic. preferably it should be a global configuration and shouldn't
> impact any of the existing tests.

- [ ] A `Ledger` in `discopy.testing`: the pass/fail history of each
  property cell, stored at `.hypothesis/proptest-ledger.json`, allocating
  each cell's example budget — boosted when the history is flaky, trimmed
  when it is long stable, the written default otherwise — with its unit
  tests in `test/testing.py`.
- [ ] A `proptest/conftest.py` that swaps each cell's budget in before it
  runs and records its outcome after, fully automatic, no test file
  edited.
- [ ] The `proptest` workflow restores the latest ledger artifact before
  the run and uploads the updated ledger after.
- [ ] PROPTEST.md and CHANGELOG.md describe the adaptive budget.
- [ ] `pflake8 discopy` and the test suites green; measure the
  warm-ledger speedup on a second run.
