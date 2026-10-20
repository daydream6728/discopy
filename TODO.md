> Let's finish the discopy-next bootstrap e.g. the wip from this PR should be merged in next and closed upstream https://github.com/discopy/discopy/pull/677/changes

Port of discopy/discopy#677 (Church arithmetic inside an exact two-stack token machine), ruled "next as notebooks, needs porting" on #2.

- [x] Measure which of #677's `closed`/`biclosed`/`cmap`/`monoidal` changes already exist on `main`
- [x] Port only the library code `neural-church.md` needs, with tests and a CHANGELOG entry
- [x] Get `docs/notebooks/neural-church.md` running on `main` under `export_notebooks.py --check`, listed in `docs/index.rst`
- [x] Decide on the three `.ipynb` notebooks of #401: translate or link
- [x] pflake8, pylint (≥ fail-under), pytest on touched tests and doctests
