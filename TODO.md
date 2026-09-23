# TODO

> about the dagger being wrongfully propagated, any way to merge the
> following branch https://github.com/discopy/discopy/pull/752 in this
> one?

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-23 19:05 Merge
      `pull/752/head` (`abc.DaggerCategory`, #731) into this branch,
      resolving the conflicts by porting its design into this branch's
      idiom: `DaggerCategory` holds the abstract `dagger` and the
      involution and contravariance laws in their `Annotated` spelling,
      `cat.Arrow`, `matrix.Matrix`, `Hypergraph` and `CMap` declare it
- [ ] Re-point or delete every reference to the moved laws: the
      inapplicable declarations of `cat.Functor` go, the type and
      diagram declarations of `rigid`, `biclosed` and `pivotal` follow
      the laws to their new home, `pivotal.Ty` keeping them
- [ ] Port the tests and the CHANGELOG entry, run the dagger cells at
      every level, classify what the runs show
- [ ] `ty check`, `ruff check`, pytest, proptest fast + targeted
      cells, close
