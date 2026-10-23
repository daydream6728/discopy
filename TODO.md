> cubic's review of 1a00a0b8 (2026-10-22):
>
> P2: `reduce` never requeues level-0 normalization after a lower-priority rewrite, so `full_reduce` can return with normalization still applicable to touched or newly created spiders. Requeue `region` for every rule level.
>
> P3: This entry overstates the rewrite guarantee: `graphlike` drops scalar factors, so each step is sound only up to a scalar, not an exact ZX equation. Say “up to a scalar” here to match the implementation and tests.
>
> P3: `circuit` resets the process-wide random generator and leaves it in a different state after every benchmark setup. Save and restore the RNG state around PyZX's generator so this benchmark remains deterministic without affecting other tests or benchmarks.
>
> P3: `Agenda.update` keeps a stale heap priority when a queued spider's incidence changes, so the advertised min-degree agenda is not maintained after rewrites. Refresh queued priorities when their degree changes.

- [ ] requeue level 0 with the region a step touched, with a test that random graph-like hypergraphs reduce to where no rule applies
- [ ] the changelog says up to a scalar
- [ ] the benchmark leaves the global random state as it was
- [ ] the agenda moves a queued spider to its current degree, measured against pyzx 0.10.7
- [ ] merge #288's head
