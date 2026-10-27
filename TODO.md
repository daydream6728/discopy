Fix rel-int/discopy-next#289 (power_fix fails when max_chi is below the photon budget: one compressed optimiser reused for every depth) as the issue describes.

- [x] `power_fix`: a fresh `QuimbBackend` optimiser for each contraction, as `fix` does
- [x] `power_fix`: the truncation warning checks every depth it contracts
- [x] regression test in `test/optyx/test_fix.py`
- [x] `CHANGELOG.md` line
- [x] pflake8, ruff, ty, pylint, pytest
