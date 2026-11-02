> Follow toumix/desire/EVENING.md

Fixes #413: feedback doctests `reset` and `time_step` fail unless markov is imported first.

- [x] find why: under `--import-mode=importlib`, a module collected before `discopy` is imported is executed twice
- [x] import `discopy` in `test/plugin.py`, before collection
- [x] `cmap.py`, `feedback.py` and `hypergraph.py` pass when run alone; full `--skip-extra` suite unchanged
