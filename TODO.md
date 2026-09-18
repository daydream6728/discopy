# TODO

> ok lets return to the generator naming scheme, rename Factory to Generator and implement the @generator decorator on FreeCategory, from which i think all of Diagram, Ty and PRO*  inherit
> about Dim and Nat, I thought most of it was resolved in the recent changes on main. Can you merge discopy/discopy:main onto this branch and find out from the CHANGELOG whether it could avoid the ad-hoc exceptions?

- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 20:00 Merge `discopy/discopy:main` into the branch and read its `CHANGELOG` for what it says about `Nat` and `Dim`.
- [ ] Rename `Factory` to `Generator` and bind a generator under the name of its class, with `@generator` on `FreeCategory`.
- [ ] Rename every `x_factory` slot to `X` across the package, tests and docs.
- [ ] Docs, lint, suite, proptest.
