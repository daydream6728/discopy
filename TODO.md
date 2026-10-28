> experiment with this in a new branch. add a new sampler that uses catalytic variables to sample diagrams with unbounded boundaries for each level of the hierarchy

Branched off `proptest/plumbing`, local experiment, after the derivation of a Boltzmann sampler for monoidal diagrams with the width as a catalytic variable.

- [ ] Symmetric levels: draw an unbounded domain and codomain port by port with `y` per port, the completion of the open wires a fixed point
- [ ] Planar levels: the walk of the leaves of the grammar of a category in normal form, its state the wires left of and from the last outputs, its completion the catalytic equation solved as a sparse linear system below its singularity
- [ ] Type the walk by unification of placeholders, each leaf derived by `discopy.boltzmann`
- [ ] Test the normal form against `monoidal.Diagram.normal_form` and the sampler against exact probabilities
- [ ] One strategy for every level, and compare on `benchmark/generators`
