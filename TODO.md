Refactor the TRMP experiment with discopy-next, abstracting the generic code into the library and keeping only the dataset specific scripts in the repo. First make sure you reproduce exactly the same results then try to beat the performance of the specialised kernel with a more generic one based on geometric deep learning.

The second of three pull requests moving the TRMP experiments onto discopy-next ([rel-int/Recursive_GNNs#1](https://github.com/rel-int/Recursive_GNNs/issues/1)): the networks, on top of the trainers.

- [x] `discopy.neural.wiring`: peer and factor tables (padded routing), from a factor table or a `from_incidence` / `from_relation` map
- [x] `discopy.neural.cell`: `Site`, `PeerSite`, `DeepSet`, `Refresh`, `HaltHead`, `gru_cell`, `Widths`, `widths_for`
- [x] `discopy.neural.recursion`: `Recursion`, `PeerNet`, `FactorNet`
- [x] bit-exact against rel-int/Recursive_GNNs at 7b4a85f (its `parity/test_model.py`, and every recipe end to end with `python -m parity check`)
- [x] tests, doctests, 100% line coverage, CHANGELOG, `test/plugin.py`
- [ ] CI green
