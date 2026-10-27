Fix rel-int/discopy-next#115 (Boxes that are not spiders claim to be cartesian) as the issue describes.

- [x] `zx.H` is neither deterministic nor affine
- [x] a quantum gate is deterministic when its array is a function on basis states, so `Bra` is, `H` and the rotations are not
- [x] `gates.Bra` and `gates.Match` are not affine
- [x] `tensor.Sum` (so `zx.Sum`, `circuit.Sum`) is a `markov.Sum`
- [x] old pickles of frobenius `Cup` and `Cap` get their flags
- [x] changelog, checks
