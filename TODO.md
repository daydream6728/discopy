> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

- [x] B52 of #31: `hopf.Functor` sends `Twist(x)` to the inverse of `F(Braid(x, x).trace())`, both handednesses, on `D(Z/3)` anyons and `Double(taft(3))`
- [x] B53 of #31: `Representation.l` is the wrong side's dual: `Intertwiner.cups(V.l, V)` and `caps(V, V.l)` are not intertwiners for Taft(3)
- [x] B17 (claim table of #606's second read): `ribbon.Braid.rotate` is wrong for dagger braids
- [x] B87 of #31, hopf part: `test/hopf.py`'s twist tests assert a trivial twist against `eye(2)`, so they cannot fail
- [x] CHANGELOG, full suite, pflake8, pylint, proptest cells `hopf or ribbon or Intertwiner`
