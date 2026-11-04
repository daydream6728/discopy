> Follow toumix/desire/EVENING.md

Fixes #434: `discopy/optyx/core/path.py` run alone fails its `Amplitudes` doctest.

- [x] find why: #413's `import discopy` does not import `discopy.optyx`, so the module is executed twice under `--import-mode=importlib`
- [x] `test/plugin.py` imports every module of `discopy` by its name before collecting it
- [x] every `discopy/` file run alone: `optyx/channel.py`, `optyx/core/diagram.py`, `optyx/core/path.py` now pass, nothing else changes
