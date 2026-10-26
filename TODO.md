# Review round: cubic on 95b38e9f

> P2 (discopy/monoidal.py:2147): `Equation.to_tree` emits nonnumeric `space` values that `Equation.from_tree` cannot reconstruct. Validate `self.space` before adding it to the tree, so serialization rejects the invalid equation instead of producing a dump that cannot be loaded.

- [ ] `monoidal.Equation.to_tree` raises on a `space` that is not a number, as `from_tree` does
