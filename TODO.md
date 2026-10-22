# TODO

> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Ruling of 10-22 on #145: https://github.com/rel-int/discopy-next/issues/145#issuecomment-6350526890
("the network is inside, the modules are outside"). On top of `claude/fix31-rep`.

- [ ] `Intertwiner[H]` is its own factory, holding `inside: tensor.Diagram` with `Representation` ends
- [ ] `>>`, `@` and dagger compose the networks and the modules; `eval`, `to_map` and `draw` delegate to `inside`
- [ ] trees carry the algebra's generators and each module's action, `eval(repr(V)) == V` kept
- [ ] `Hypergraph[Intertwiner[taft(3)]]`, or say that the network inside is what gets the hypergraph
- [ ] doctests and tests go through `.inside` where they meet a network; CHANGELOG under `### Changed`
