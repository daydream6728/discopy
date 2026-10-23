> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Rulings: https://github.com/rel-int/discopy-next/issues/168#issuecomment-6349668135 and https://github.com/rel-int/discopy-next/issues/31#issuecomment-6360707328

- [ ] #168 encoding: extend the complex convention of #775, no version key. `dumps` writes factory-tagged nodes for ndarrays, numpy scalars and tuples, and a sympy expression becomes a tree of whitelisted sympy classes, so `loads` never calls `sympify` or `eval`. No existing tree changes shape.
- [ ] #168 scope: a tree for finite data only. `to_tree`/`from_tree` for `interaction`, `para`, `CQ`, `Equation` and functors whose maps are dicts. For `python.Function`, `Stream`, functors with callables and `Drawing`, serialisation is declared inapplicable and raises with a message saying why.
- [ ] B86 hash: field hash on `para.Symmetric`, `interaction.Ty` and `interaction.Diagram`; `Stream` and `stream.Ty` stay unhashable.
