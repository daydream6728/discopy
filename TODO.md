# Boxes 29 and 30 of #314: the Perceval backend drops `Matrix.scalar` and sums probabilities

Autonomous 🌙 Evening round of 2026-11-02, under
[`daydream6728/desire`](https://github.com/daydream6728/desire)'s `EVENING.md`, step 5: *"in the
next repos, finish every item left"*, taking the next repo's bugs that need no decision. No human
prompt: the two boxes are
[#314](https://github.com/rel-int/discopy-next/issues/314)'s own, each stating its oracle.

> - [x] `PercevalBackend` sums the probabilities of the terms of a sum, so interference is lost:
>   `Create(1) + Create(1) @ Scalar(-1)` gives `{(1,): 1.0}` where quimb finds zero; sum
>   amplitudes, then take the Born rule
> - [x] `PercevalBackend` ignores `Matrix.scalar` and the normalisation `dilate()` adds: the
>   amplitude of `Create(1) @ Scalar(1j)` is 1, quimb's 1j

- [x] Reproduce both boxes against this `main`, and say which of the two the reported symptom belongs to
- [x] Carry `scalar` and `normalisation` out of `path.Matrix` into the Perceval result
- [x] Sum a sum's amplitudes, then take the Born rule
- [x] Tests pinning both against the quimb and permanent backends
- [x] `CHANGELOG.md`
- [x] `pflake8`, `pylint`, `ruff`, `ty` and the optyx suite

Measured while taking them, and both go in the pull request rather than on #314:

- the cancelling example box 29 states was wrong for box 30's reason as well. In the `amps` task
  this tree already summed the terms coherently; what made `Create(1) + Create(1) @ Scalar(-1)`
  read as `2` there was the dropped `Scalar(-1)`, so the stated cause — *"sums the probabilities
  of the terms"* — is only the `probs` task's, and only once the scalar is carried
- the factor `dilate` adds was lost to Perceval's own renormalisation, not to the arithmetic:
  `Simulator.evolve` returns a unit vector once a postselection is set, where `prob_amplitude`
  does not
