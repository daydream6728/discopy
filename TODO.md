Refactor the TRMP experiment with discopy-next, abstracting the generic code into the library and keeping only the dataset specific scripts in the repo. First make sure you reproduce exactly the same results then try to beat the performance of the specialised kernel with a more generic one based on geometric deep learning.

The first of three pull requests moving the TRMP experiments onto discopy-next ([rel-int/Recursive_GNNs#1](https://github.com/rel-int/Recursive_GNNs/issues/1)): the trainers. The networks and the geometric backend stack on it.

- [x] `discopy.neural.train`: seeding, AdamW on matrices, cosine schedule, bias-corrected EMA, per-sample gradient clip
- [x] `discopy.neural.lattice`: lattice deduction, its persistent pool and the chain search
- [x] `discopy.neural.act`: halting losses, the slot pool, rollouts
- [x] bit-exact against rel-int/Recursive_GNNs at 7b4a85f (its `parity/test_training.py`)
- [x] tests, doctests, 100% line coverage, CHANGELOG, `test/plugin.py`
- [ ] CI green
