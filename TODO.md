> ok back into experiment mode for the open questions:
> using permutations, temperley-lieb, brauer, and double finite functions for frobenius, investigate whether we can separate the boxes from plumbing and devise a more structure-aware sampler.
> what would be the analog of size/energy when sampling plumbing?

Branched off `proptest/boltzmann`, local experiment.

- [x] State the decomposition: a diagram of a traced symmetric, compact, Markov or hypergraph category is a set of boxes and one plumbing morphism of the free such category on objects alone, a bijection, a Brauer diagram, a finite function or a cospan
- [x] Sample plumbing on the line of ports, weighted by `q` per crossing, by a transfer matrix on the number of open wires: exact, linear in the ports times the open wires
- [x] Sample boxes and plumbing jointly, `x` per box over `k!`, exactly, conditioned on the number of boxes, which Hypothesis draws
- [x] Type the wires after the fact, one colour per spider, and build the diagram through `Hypergraph`
- [x] Test the exact laws on small lines by enumeration
- [x] Compare with the derivation sampler and the graph sampler on `benchmark/generators`: samples and broken laws
- [x] Write up the energy of plumbing and the results
