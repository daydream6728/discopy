# TODO

> next project: discopy as an algebraic implementation of all deep learning architectures
> starting with geometric deep learning: define a group (from simple ones and algebraic operations eg direct, free and wreath products) get an equivariant neural net or a data augmentation pipeline from it
> another direction: lattice deduction transformers

Slice 1 of [#121](https://github.com/rel-int/discopy-next/issues/121): permutation representations, groups as normal forms (toumix, live 2026-10-19).

- [WIP] @session_01QMSgF6Gi6dsiacsxBoC45c-2026-10-19 12:50 `abc.Groupoid` (dagger is inverse, `invertibility` law) and `abc.Group`, a groupoid with one object; `finset.Permutation` is a groupoid
- [ ] `discopy.group`: `Cyclic[n]`, `Symmetric[n]`, `Product[G, H]`, `Wreath[G, H]` as normal forms with generators, words, order, elements and uniform sampling
- [ ] `Action`: a functor into `finset.Permutation` by the images of the generators, natural actions, product action, imprimitive and product actions of a wreath, tensor and orbits
- [ ] the sudoku group as an example, of order 1,218,998,108,160
- [ ] the group laws in the property matrix, tests, docs page, `CHANGELOG.md`
