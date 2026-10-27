Fix rel-int/discopy-next#254 (zw.ZBox with a list of amplitudes crashes in conjugate) as the issue describes.
Fix rel-int/discopy-next#258 (BitControlledPhaseShift declares a classical codomain) as the issue describes.
Fix rel-int/discopy-next#297 (Scalar fails on any sympy expression but a symbol or a product) as the issue describes.

- [ ] #254: `ZBox.conjugate` goes through `np.conj`, as `dagger` does, with a regression test
- [ ] #258: `BitControlledPhaseShift` has codomain `qmode**n_modes`, with a regression test
- [ ] #297: already fixed on `main` by 5ebb44e3 (#276): add the issue's cases as a regression test
- [ ] CHANGELOG.md `[Unreleased]`
- [ ] pflake8, ruff, ty, pylint, pytest --skip-extra, doctests
