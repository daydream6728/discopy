# cubic's round on #430

> P2: Guard the witness before dividing. A zero-success postselection can leave a non-empty
> result with zero amplitudes, so `bare / result[witness]` raises or produces invalid values
> instead of returning the zero amplitude/probability result.

> P3: The new changelog sentence is grammatically broken at `cannot — the global scalar`. Add
> `that` after "factors" and use a colon before the two factors so the release note is readable.

- [ ] Measure what a zero-success postselection does give, on this head and on the merge base
- [ ] Guard the witness, and carry whatever the measurement says about the amplitude itself
- [ ] A test over a selection no photon number can satisfy
- [ ] `CHANGELOG.md`, the grammar and anything the round adds
- [ ] `pflake8`, `pylint`, `ruff`, `ty` and the optyx suite
