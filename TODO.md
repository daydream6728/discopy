# TODO

Review round, cubic on #433:

> P2: `prob_with_perceval` does not reject an impossible photon count like `eval` does. With
> multiple open output modes, a negative remaining photon count produces an empty occupation list
> and silently returns a zero-column result; compute and validate `n_photons_out` before
> enumerating it.

Valid, and worse than it says: `occupation_numbers(-1, 1)` is `[(-1,)]`, a *negative* occupation.
Measured on this head — `Select(2) @ Id(2)` at `n_photons=1` returns a `(3, 0)` matrix where
`prob()` raises, and `Select(2)` alone raises perceval's *"Can't put -2 photons in zero modes!"*
rather than the library's own error. Two backends for one quantity agree on what is impossible too.

- [ ] Raise `eval`'s own `ValueError` on a negative photon count out
- [ ] A test that both branches reject the same diagram
