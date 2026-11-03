# TODO

Review round, cubic on #433:

> P2: `as_tensor=True` passes all `output_occ` entries to `amplitudes_2_tensor`, although this
> result has columns only for filtered `selections`; selected diagrams therefore index past the
> last column. Build the tensor with each selected state's open-mode occupation instead.

Valid, and it predates the head: `prob(as_tensor=True, with_perceval=True)` raises `IndexError` on
`main` too for any diagram with a selection. The oracle is the same method's other branch, whose
`eval(as_tensor=True)` builds the codomain from `occupation_numbers(n_photons_out, index(cod))`.

- [x] Build the surviving output states from the open-mode occupations instead of filtering, so
      the column order is a construction rather than a coincidence of `occupation_numbers`
- [x] Hand `amplitudes_2_tensor` those open-mode occupations
- [x] A test that the two branches agree as tensors on a selected diagram
- [x] `CHANGELOG.md`: the crash is user-facing
