# TODO

> ok lets return to the generator naming scheme, rename Factory to Generator and implement the @generator decorator on FreeCategory, from which i think all of Diagram, Ty and PRO*  inherit
> about Dim and Nat, I thought most of it was resolved in the recent changes on main. Can you merge discopy/discopy:main onto this branch and find out from the CHANGELOG whether it could avoid the ad-hoc exceptions?

- [x] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 20:00 Merge `discopy/discopy:main`: nothing to merge, its head `6008fd79` is the merge base of this branch.
- [x] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 20:00 Read what `main` says about `Nat` and `Dim`: `List[X]` sets its generator through the `NamedGeneric` subscript, so it is not an exception, while `Nat` and `Dim` extend `Ty` rather than `List[int]` and keep theirs by hand. `monoidal.Diagram.__call__` reads `self.dom.ob.generator_factory` on whichever free monoid `ob` is, so that one slot is named after a role rather than a class.
- [x] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 20:00 Rename `Factory` to `Generator`.
- [ ] Name the decorator: `generator` is a property on `Arrow`, `Ty`, `Sum`, `Layer` and `Diagram`, all below `FreeCategory`, so a classmethod of that name is shadowed on every class that would use it. Waiting on a name.
- [ ] Rename every other `x_factory` slot to `X` and bind it with the decorator.
- [ ] Docs, lint, suite, proptest.
