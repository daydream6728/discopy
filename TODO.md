> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `decoder`: the decoders `Hypergraph.to_diagram` and `CMap.to_diagram`, and the `make_monogamous` / `make_causal` they call.

- [x] B71 of #31: `CMap.to_diagram` places every domain-less box at the right of the scan, so `(s @ x).to_map().to_diagram()` raises `NOT_SYMMETRIC` in monoidal, rigid and pivotal and is `x @ s >> Swap` in symmetric; place it in its face instead
- [x] B71 of #31: `CMap.make_causal` cuts merely-backward wires whenever a scalar loop is present, against its docstring
- [x] #187: a cap decoded by `Hypergraph.make_monogamous` has no offset, so `(f @ Cap(x, x)).to_hypergraph().to_diagram()` permutes; give it the offset where its first consumer reads it, without regressing #108
- [x] `Hypergraph.make_causal` asks a category without merges for a `spider_factory`, e.g. `compact.Box('g', x, x).transpose().depth()` raises `AttributeError` (found by agent `hypergraph`)
- [ ] check numerically: a tensor functor on random planar, symmetric and compact diagrams through both decoders
- [ ] CHANGELOG, full suite, pflake8, pylint
