Fix rel-int/discopy-next#294 (PercevalBackend fails on a closed diagram) as the issue describes.
Fix rel-int/discopy-next#295 (Diagram.from_perceval misreads a negative feed-forward offset) as the issue describes.
Fix rel-int/discopy-next#299 (Diagram.from_perceval drops a detector with nothing after it) as the issue describes.

- [ ] #294: `PercevalBackend._process_io` turns every selection of a closed diagram into the effect
- [ ] #295: a negative offset `k` leaves `-k - 1` modes between circuit and measured modes
- [ ] #299: `Diagram.from_perceval` adds the trailing detectors of `p.detectors`
- [ ] regression tests, CHANGELOG line
- [ ] pflake8, ruff, ty, pylint, pytest
