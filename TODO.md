# cubic's round on #430

> P2: Guard the witness before dividing. A zero-success postselection can leave a non-empty
> result with zero amplitudes, so `bare / result[witness]` raises or produces invalid values
> instead of returning the zero amplitude/probability result.

> P3: The new changelog sentence is grammatically broken at `cannot — the global scalar`. Add
> `that` after "factors" and use a colon before the two factors so the release note is readable.

- [x] Measure what a zero-success postselection does give, on this head and on the merge base
- [x] Guard the witness, and carry whatever the measurement says about the amplitude itself
- [x] A test over a selection no photon number can satisfy
- [x] `CHANGELOG.md`, the grammar and anything the round adds
- [x] `pflake8`, `pylint`, `ruff`, `ty` and the optyx suite

What the measurement said, and it is more than the guard: the witness is not where a zero-success
postselection ends up. `Create(1) >> Select(2)` raised `TypeError` from the SLOS backend on the
`amps` task **on the merge base as well**, because `prob_amplitude` indexes the Fock space of the
state's photon number and an effect outside it has no index; and the `probs` task, which used
`sim.probs`, answered `1.0` for it and `0.5` for
`Create(1, 0) >> BS >> Select(2, 0)` — both zero everywhere else. Routing probabilities through
amplitudes made this head reach the crash too, so the round carries the law rather than the guard:
a circuit of linear optics conserves photon number, so an effect counting a different number is an
amplitude of zero. The witness guard stays for the other way a vector can be all zeros.
