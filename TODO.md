# TODO

> removed the functor refactor from claude/nifty-cray-b7mtqd, can you
> update this branch with that deletion?

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-20 14:10 Revert the
      "Let a generator say how a functor maps it" round (`6f78b24` to
      `0c2de09`: the `image` methods, the `interprets` gate, the
      dispatcher `cat.Functor.__call__` and the seven Functor classes
      it let the `Generator` machinery build), resolving the revert
      against everything built on top since the merge
- [ ] Drop the round's CHANGELOG entry and reconcile the entries that
      reference it
- [ ] `ty check`, `ruff check`, pytest, proptest fast profile, close

Note: `origin/claude/nifty-cray-b7mtqd` still points at `0c2de09`, the
refactor itself, so there is no upstream deletion to merge; this round
reverts the refactor here instead.
