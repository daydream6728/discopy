# TODO

> in a new experimental branch based off this one, and which you are going to
> push on my fork at origin (daydream6728/discopy) instead of upstream
> (discopy/discopy), make a global refactor removing all uses of + as tensor

- [ ] `monoidal.List`: drop `cast`/`__add__`/`__radd__`/`__mul__`/`__rmul__`, move `__pow__` up from `Ty`
- [ ] `python.multiplicative`: `tensor`, `swap`, `permutation`, `copy`
- [ ] `python.additive`: `tensor`, `swap`, `permutation`, `merge`
- [ ] `abc.SymmetricCategory.permutation` and `symmetric.Diagram.permutation`
- [ ] `hypergraph.from_graph`
- [ ] `stream.Ty` and `stream.Stream`
- [ ] `interaction.Ty`
- [ ] `para.Symmetric`
- [ ] `grammar.categorial.BinaryTerm`
- [ ] drop the `__add__ = __matmul__` aliases (`interaction`, `stream`, `quantum.channel`)
- [ ] `matrix.Matrix.ob = int`: the last raw-int monoid, blocks `interaction.Ty[int]`
- [ ] tests, CHANGELOG, `pflake8` + `pytest`
