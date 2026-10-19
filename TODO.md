# TODO

cubic's review of this pull request, 2026-10-19, quoted:

> **5 issues found** across 15 files
> - CONTRIBUTING.md:138 — P3: The plugin does not end every run with this section: runs with no collected cell and neither report option return without printing it. [...]
> - proptest/report.py:113 — P2: `XPASSED` is explicitly a checked outcome, but this condition and `render` recognize only `PASSED`. [...]
> - proptest/report.py:115 — P2: `distinct < budget` proves only that this run observed duplicate or missing draws, not that the strategy's support is exhausted. [...]
> - proptest/report.py:233 — P2: This clean-baseline message counts every baseline entry even though `stopped()` compares only `CHECKED` outcomes. [...]
> - discopy/drawing/__init__.py:139 — P3: The returned GIF has no accessible name [...]

- [ ] `CONTRIBUTING.md`: every run *of the matrix*
- [ ] an unexpected pass: answered on the thread, excluded by design (`test_only_a_passing_cell_can_be_exhausted`)
- [ ] `Cell.exhausted` says what fewer distinct terms does and does not show
- [ ] the clean-baseline line counts the cells the baseline checked
- [ ] `to_gif`'s `<img>` has an `alt`
