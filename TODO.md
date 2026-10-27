Fix rel-int/discopy-next#289 (power_fix fails when max_chi is below the photon budget: one compressed optimiser reused for every depth) as the issue describes.

- [ ] `power_fix`: a fresh `QuimbBackend` optimiser for each contraction, as `fix` does
- [ ] `power_fix`: the truncation warning checks every depth it contracts
- [ ] regression test in `test/optyx/test_fix.py`
- [ ] `CHANGELOG.md` line
- [ ] pflake8, ruff, ty, pylint, pytest
