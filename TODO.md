Fix rel-int/discopy-next#376 (dumps fails on a Fraction phase) as the issue describes.

- [ ] `encode`/`decode` write and read a `Fraction` as a factory-tagged node, as `complex`
- [ ] doctests and a regression test on a `zx.Z` spider with a `Fraction` phase
- [ ] `CHANGELOG.md` line
- [ ] pflake8, ruff, ty, pylint, pytest
