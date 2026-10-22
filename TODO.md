Refactor the TRMP experiment with discopy-next, abstracting the generic code into the library and keeping only the dataset specific scripts in the repo. First make sure you reproduce exactly the same results then try to beat the performance of the specialised kernel with a more generic one based on geometric deep learning.

The third of three pull requests moving the TRMP experiments onto discopy-next ([rel-int/Recursive_GNNs#1](https://github.com/rel-int/Recursive_GNNs/issues/1)): a generic backend for the networks, from their symmetry group.

- [x] `discopy.neural.wiring`: the blocks of a group action, `chains`, `Block`, `decompose`, `families`
- [x] `discopy.neural.geometric`: block operators, `Peers`, `Factors`, `fold`, the `Geometric` mixin
- [x] equal to the reference networks to rounding (float64 tests), gradients included
- [x] measured against the specialised kernels (rel-int/Recursive_GNNs `bench.py`)
- [ ] CI green
