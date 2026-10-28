# TODO

Prompt (scheduled routine, 2026-10-28):

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

🐦 Birdsong's plan for the night, on the day PR
[memory#114](https://github.com/daydream6728/memory/pull/114):

> **Tonight 🌙 takes next#298 then next#286, and leaves next#249 alone.**
> [#298](https://github.com/rel-int/discopy-next/issues/298)
> (`compile_to_semm` recursing forever on a multi-path cover) states the
> round-trip that settles it, so the fix picks nothing;
> [#286](https://github.com/rel-int/discopy-next/issues/286) (`is_convex`
> walking the whole downstream cone — 2.04 s at n=4,000) argues its own fix
> from acyclicity and leaves the predicate alone;
> [#249](https://github.com/rel-int/discopy-next/issues/249) ends on *"either
> updating them … or removing the stale ones"* and is a question before it is
> a fix. Say otherwise on any of the three and 🌙 follows.

- [ ] #298: `add_fusion_order` closes its past set iteratively, and
      `compile_to_semm` round-trips on a cover of more than one path
- [ ] #286: `is_convex` stops at the last box that writes into the image,
      where the host's box order is topological
- [ ] both: tests, `CHANGELOG.md`, and the local checks of `CONTRIBUTING.md`
