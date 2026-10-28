# TODO

cubic round 1 on #401:

> P2: This key collapses parallel fusions between the same two nodes, so
> `fn_to_semm` emits multiple fusion photons but `_get_fusion_photons` retains
> only the last pair and then raises `KeyError` for the first photon. Track
> each fusion occurrence (or fusion object) separately rather than keying only
> by `(node, nbr)`.

- [x] pair the photons of a pair of nodes by occurrence, and a test for two
      parallel fusions
